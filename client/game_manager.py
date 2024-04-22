import time
from collections import deque
from queue import Queue

import panda3d.core as p3d

from typing import Union
from direct.showbase import ShowBase
from direct.task import Task


from client.connection.waiting_screen import WaitingScreen

from common.collision.setup import setup_collisions
from common.config import TIME_STEP
from common.objects.bullet import Bullet
from common.objects.bullet_factory import BulletFactory
from common.state.game_state_diff import GameStateDiff
from common.state.player_state_diff import PlayerStateDiff
from common.tiles.tile_controller import create_new_tile
from common.player.player_controller import PlayerController
from common.tiles.tile_node_path_factory import TileNodePathFactory
from common.transfer.network_transfer import NetworkTransfer
from common.typings import TimeStep


class GameManager:
    def __init__(self, game: ShowBase, node_path_factory: TileNodePathFactory):
        # all players by ids
        self.players: dict[str, PlayerController] = {}

        # main player displayed model and more accurate invisible model used for reference
        self.main_player: Union[None, PlayerController] = None
        self.main_player_server_view: Union[None, PlayerController] = None
        self.active_players = 0

        # frame by frame diffs to apply on server state if it lags behind
        self.game_state_diffs: deque[GameStateDiff] = deque()

        # previous state to calculate diff with current state
        self.last_game_state: GameStateDiff = GameStateDiff(TimeStep(begin=0, end=time.time() - 0.2))

        # current game state
        self.game_state: GameStateDiff = GameStateDiff(TimeStep(begin=0, end=time.time() - 0.1))

        # buffer of server states for entity interpolation
        self.server_game_state_transfer_deque: deque[GameStateDiff] = deque()

        # flag to set if new server game state is expected to be processed on next frame
        self.tick_update = False

        # delay for other player state update
        # it allows for interpolation between previous server states
        # should be kept relatively low (i.e. 100ms) to not be noticeable
        self.other_players_delay = 2 * TIME_STEP

        self.bullet_factory = BulletFactory(game.render)
        self.bullets: list[Bullet] = []

        self.game = game
        self.node_path_factory = node_path_factory
        self.sync_tasks: dict[str, Task] = {}

        self.waiting_screen = WaitingScreen(game.loader)

    def setup_player(self, player_state: PlayerStateDiff):
        player_node_path = self.node_path_factory.get_player_model()
        player_node_path.reparent_to(self.game.render)
        player = PlayerController(
            player_node_path,
            player_state
        )
        player.sync_position()

        self.game_state.player_state[player_state.id] = player_state
        self.players[player_state.id] = player
        self.active_players += 1
        if self.active_players >= self.game.expected_players:
            self.waiting_screen.hide()
            self.game.attach_input()
        else:
            self.waiting_screen.update(self.active_players, self.game.expected_players)

        return player

    def set_main_player(self, player: PlayerController):
        self.main_player = player
        self.game.taskMgr.add(self.sync_game_state, "sync game state", sort=1)
        self.game.taskMgr.add(self.game_state_snapshot, "store game state diffs", sort=2)
        self.game.accept("bullet-into-wall", self.handle_bullet_wall_hit)
        self.game.accept('player' + player.get_id() + '-into-flag', self.game.handle_flag, [self.main_player])

        # add collider to main player controller
        player_collider = player.colliders[0]
        self.game.cTrav.addCollider(player_collider, self.game.pusher)
        self.game.pusher.addCollider(player_collider, player_collider)

        # add another controller for the player that doesn't directly respond to input
        # but is set to server state as it arrives i.e. every 3 frames and updated afterward
        # the difference in position of this object and main player controller
        # can be linearly interpolated to present smooth motion
        # while being "mostly" correct compared to server version
        model = self.node_path_factory.get_player_model()
        model.reparent_to(self.game.render)
        self.main_player_server_view = PlayerController(
            model,
            player.state.clone(),
            ghost=True  # todo: implement "don't show" better; see inside PlayerController
        )
        self.main_player_server_view.sync_position()

    def sync_game_state(self, task):
        if self.tick_update:
            self.tick_update = False
            server_game_state = self.server_game_state_transfer_deque[-1]
            self.apply_local_diffs(server_game_state)
            self.update_positions_and_reconciliate(server_game_state)
        else:
            self.update_main_player_position()
        self.interpolate_other_players_positions()
        self.update_bullets()
        return task.cont

    def update_bullets(self):
        for bullet in self.bullets:
            bullet.update_position()

    def shoot_bullet(self) -> p3d.Vec3:
        direction = self.main_player.get_state().get_direction()
        bullet = self.bullet_factory.get_one(
            (self.main_player.get_state().get_position() + p3d.Vec3(0, 0, 0.5)
             + direction * 0.5),
            direction,
            self.main_player.get_id()
        )
        self.bullets.append(bullet)
        return direction

    def handle_bullet_wall_hit(self, entry):
        if "wall" in entry.get_into_node_path().get_name():
            bullet_id = entry.get_from_node_path().get_tag('id')
            self.bullets = [b for b in self.bullets if b.bullet_id != bullet_id]
            self.bullet_factory.destroy(int(bullet_id))

    def apply_local_diffs(self, server_game_state: GameStateDiff):
        """
        Applies diffs between the time when server had built
        the game state and the time data arrived locally
        """
        while len(self.game_state_diffs) > 0:
            state = self.game_state_diffs.popleft()
            if state.step.end < server_game_state.step.end:
                # print("[DIFF] Discarding", state.step)
                continue
            else:
                server_game_state.apply(state)
                # print("[DIFF] Applying", state.step)
                while len(self.game_state_diffs) > 0:
                    state = self.game_state_diffs.popleft()
                    server_game_state.apply(state)
                    # print("[DIFF] Applying", state.step)
                break

    def update_positions_and_reconciliate(self, server_game_state: GameStateDiff):
        """
        Perform client side reconciliation
        and smooth out player movement using interpolation
        """
        # print("[DIFF] Server state at {} vs now {}, history len = {}".format(
        #     server_game_state.step.end, time.time(), len(self.game_state_diffs)))
        for player in self.players.values():
            if player is not self.main_player:
                player.replace_state(server_game_state.player_state[player.get_id()])
                player.sync_position()
            else:
                self.main_player_server_view \
                    .replace_state(server_game_state.player_state[player.get_id()])
                self.main_player_server_view.sync_position()
                self.main_player.update_position()
                lerp = self.main_player.state.motion_state \
                    .lerp(0.3, self.main_player_server_view.state.motion_state)
                self.main_player.state.motion_state.apply(lerp)
                self.main_player.sync_position()

    def update_main_player_position(self):
        """
        Interpolate player positions when no server game state update arrived
        by moving both positions simultaneously and once again
        reducing the difference by given fraction (lerp)
        """
        last_player_position = self.main_player.state.clone()
        self.main_player.update_position()
        diff = last_player_position.diff(self.main_player.state)
        self.main_player_server_view.state.apply(diff)
        self.main_player_server_view.sync_position()
        lerp = self.main_player.state.motion_state \
            .lerp(0.3, self.main_player_server_view.state.motion_state)
        self.main_player.state.motion_state.apply(lerp)
        self.main_player.sync_position()

    def interpolate_other_players_positions(self):
        """
        Show other players movement self.other_players_delay ms in the past
        """
        if len(self.server_game_state_transfer_deque) == 0:
            return

        target_time = time.time() - self.other_players_delay
        i = 0
        while i < len(self.server_game_state_transfer_deque):
            if self.server_game_state_transfer_deque[i].step.end < target_time:
                i += 1
            else:
                break
        else:
            # target_time is ahead of all known states - use the most recent
            state: PlayerStateDiff
            for id, state in self.server_game_state_transfer_deque[-1].player_state.items():
                if id == self.main_player.get_id():
                    continue
                self.players[id].replace_state(state.clone())
                self.players[id].sync_position()
            return

        # i-th state is our best guess
        # make a diff with prior one, cut it to target_time and apply
        if i <= 0:
            # prior state doesn't exist - we can't get diff - use what we have
            for id, state in self.server_game_state_transfer_deque[i].player_state.items():
                if id == self.main_player.get_id():
                    continue
                self.players[id].replace_state(state.clone())
                self.players[id].sync_position()
            return
        prior_state = self.server_game_state_transfer_deque[i-1].clone()
        diff = prior_state.diff(self.server_game_state_transfer_deque[i])
        for id, state in diff.player_state.items():
            if id == self.main_player.get_id():
                continue
            self.players[id].replace_state(prior_state.player_state[id])
            lerp = state.motion_state.cut_end(target_time)
            self.players[id].state.motion_state.apply(lerp)
            self.players[id].sync_position()

    def game_state_snapshot(self, task):
        self.game_state_diffs.append(
            self.last_game_state.diff(self.game_state)
        )
        return task.cont

    def queue_server_game_state(self, transfer: NetworkTransfer):
        server_game_state = GameStateDiff.empty(self.game_state.player_state.keys())
        server_game_state.restore(transfer)
        self.server_game_state_transfer_deque.append(server_game_state)
        while len(self.server_game_state_transfer_deque) > 5:
            self.server_game_state_transfer_deque.popleft()
        self.tick_update = True

    def setup_map(self, game, tiles, map_size):
        game.disableMouse()

        properties = p3d.WindowProperties()
        properties.set_size(1280, 800)
        game.win.request_properties(properties)

        point_light_node = game.render.attach_new_node(p3d.PointLight("light"))
        point_light_node.set_pos(0, -10, 10)
        game.render.set_light(point_light_node)

        setup_collisions(game, tiles, map_size, self.bullet_factory)

        def update_camera(task):
            if self.main_player is None:
                return task.cont
            game.camera.set_pos(self.main_player.model.getX(), self.main_player.model.getY() - 10, 15)
            game.camera.look_at(self.main_player.model)
            return task.cont

        game.taskMgr.add(update_camera, "update camera")

        for tile_data in tiles:
            tile = create_new_tile(game.loader, tile_data["node_path"], tile_data["pos"], tile_data["heading"])
            tile.reparent_to(game.render)

        if self.active_players < self.game.expected_players:
            self.waiting_screen.display()

