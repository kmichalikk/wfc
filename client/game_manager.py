import time
from collections import deque
import panda3d.core as p3d
from typing import Union
from direct.task import Task

from direct.task.TaskManagerGlobal import taskMgr
from client.connection.connection_manager import ConnectionManager
from client.game import Game
from client.screens.player_stats import PlayerStats
from common.config import MAP_SIZE, BULLET_ENERGY, TIME_STEP
from common.objects.bolt_factory import BoltFactory
from common.objects.bullet import Bullet
from common.objects.bullet_factory import BulletFactory
from common.objects.cloud_factory import CloudFactory
from common.objects.flag import Flag
from common.state.game_state_diff import GameStateDiff
from common.state.player_state_diff import PlayerStateDiff
from common.tiles.tile_controller import create_new_tile
from common.player.player_controller import PlayerController
from common.tiles.tile_node_path_factory import TileNodePathFactory
from common.transfer.network_transfer import NetworkTransfer
from common.typings import TimeStep, Input


class GameManager:
    def __init__(self, game: Game, node_path_factory: TileNodePathFactory, connection_manager: ConnectionManager):
        # all players by ids
        self.__players: dict[str, PlayerController] = {}

        # main player displayed model and more accurate invisible model used for reference
        self.__main_player: Union[None, PlayerController] = None
        self.__main_player_server_view: Union[None, PlayerController] = None
        self.__active_players = 0

        # frame by frame diffs to apply on server state if it lags behind
        self.__game_state_diffs: deque[GameStateDiff] = deque()

        # previous state to calculate diff with current state
        self.__last_game_state: GameStateDiff = GameStateDiff(TimeStep(begin=0, end=time.time() - 0.2))

        # current game state
        self.__game_state: GameStateDiff = GameStateDiff(TimeStep(begin=0, end=time.time() - 0.1))

        # buffer of server states for entity interpolation
        self.__server_game_state_transfer_deque: deque[GameStateDiff] = deque()

        # flag to set if new server game state is expected to be processed on next frame
        self.__tick_update = False
        self.__lerp_factor = 0.2

        # delay for other player state update
        # it allows for interpolation between previous server states
        # should be kept relatively low (i.e. 100ms) to not be noticeable
        self.__other_players_delay = 2 * TIME_STEP

        self.__game = game
        self.__loader = self.__game.get_loader()

        self.__bullet_factory = BulletFactory(self.__game.get_render())
        self.__bullets: list[Bullet] = []

        self.__flag = Flag(self.__game)

        self.__bolts_set_up = False
        self.__bolt_factory = BoltFactory(self.__loader, self.__game.get_render())

        self.__game_has_started = False
        self.__node_path_factory = node_path_factory
        self.__connection_manager = connection_manager
        self.__sync_tasks: dict[str, Task] = {}

    def setup_player(self, player_state: PlayerStateDiff):
        player_node_path = self.__node_path_factory.get_player_model(player_state.id)
        player_node_path.reparent_to(self.__game.get_render())
        player = PlayerController(
            player_node_path,
            player_state,
        )
        player.sync_position()
        player.set_cloud_factory(CloudFactory(self.__loader, self.__game.get_render()))
        self.__game.taskMgr.do_method_later(0.05, player.task_emit_cloud, 'emit cloud')

        self.__game_state.player_state[player_state.id] = player_state
        self.__players[player_state.id] = player
        self.__active_players += 1

        return player

    def get_active_players_count(self):
        return self.__active_players

    def get_main_player_id(self):
        return self.__main_player.get_id() if self.__main_player else ''

    def get_main_player_username(self):
        return self.__main_player.get_username() if self.__main_player else ''

    def update_input(self, inp: Input):
        self.__main_player.update_input(inp)

    def set_game_has_started(self):
        self.__game_has_started = True

    def has_game_started(self):
        return self.__game_has_started

    def set_main_player(self, player: PlayerController):
        self.__main_player = player
        self.__game.taskMgr.add(self.sync_game_state, "sync game state", sort=1)
        self.__game.taskMgr.add(self.game_state_snapshot, "store game state diffs", sort=2)
        self.__game.accept("bullet-into-wall", self.handle_bullet_wall_hit)
        self.__game.accept('player' + player.get_id() + '-into-flag', self.__request_flag_pickup)
        for i in range(0, MAP_SIZE // 2):
            self.__game.accept('player' + player.get_id() + '-into-bolt' + str(i), self.__request_bolt_pickup)

        self.__game.add_colliders_from(self.__main_player)

        # add another controller for the player that doesn't directly respond to input
        # but is set to server state as it arrives i.e. every 3 frames and updated afterward
        # the difference in position of this object and main player controller
        # can be linearly interpolated to present smooth motion
        # while being "mostly" correct compared to server version
        model = self.__node_path_factory.get_player_model(player.get_id())
        model.reparent_to(self.__game.get_render())
        self.__main_player_server_view = PlayerController(
            model,
            player.state.clone(),
            ghost=True  # todo: implement "don't show" better; see inside PlayerController
        )
        self.__main_player_server_view.sync_position()

        # show UI
        self.player_stats = PlayerStats(self.__loader, player.get_id())
        self.player_stats.display()
        self.player_stats.set_energy(10)

    def sync_game_state(self, task):
        if self.__tick_update:
            self.__tick_update = False
            server_game_state = self.__server_game_state_transfer_deque[-1]
            self.apply_local_diffs(server_game_state)
            self.update_positions_and_reconciliate(server_game_state)
        else:
            self.update_main_player_position()
        self.interpolate_other_players_positions()
        self.update_bullets()
        if self.__game_has_started:
            self.lose_energy()

        return task.cont

    def lose_energy(self):
        self.player_stats.set_energy(self.__main_player.get_energy())
        if self.__main_player.get_energy() > 0:
            self.__main_player.lose_energy()

            if self.__main_player.get_energy() <= 0:
                print("[INFO] Out of energy")
                self.__main_player.freeze()
                self.__game.taskMgr.do_method_later(
                    0,
                    lambda _: self.__connection_manager.send_freeze_trigger(self.__main_player.get_id()),
                    "send input on next frame"
                )

    def resume_player(self):
        self.__main_player.resume()
        self.__main_player.charge_energy()

    def update_bullets(self):
        for bullet in self.__bullets:
            bullet.update_position()

    def shoot_bullet(self) -> Union[p3d.Vec3, None]:
        direction = self.__main_player.try_shooting()
        if direction is not None:
            self.__main_player.lose_energy(BULLET_ENERGY)
            bullet = self.__bullet_factory.get_one(
                (self.__main_player.get_state().get_position() + p3d.Vec3(0, 0, 0.5)
                 + direction * 0.5),
                direction,
                self.__main_player.get_id()
            )
            self.__bullets.append(bullet)
        return direction

    def handle_bullet_wall_hit(self, entry):
        if "wall" in entry.get_into_node_path().get_name():
            bullet_id = entry.get_from_node_path().get_tag('id')
            self.__bullets = [b for b in self.__bullets if b.bullet_id != bullet_id]
            self.__bullet_factory.destroy(int(bullet_id))

    def __request_flag_pickup(self, entry):
        taskMgr.do_method_later(0, lambda _: self.__connection_manager.send_flag_trigger(self.get_main_player_id()),
                                "send input on next frame")

    def __request_bolt_pickup(self, entry):
        bolt_id = entry.getIntoNodePath().node().getName()[-1]
        player_id = entry.getFromNodePath().node().getName()[-1]
        player = self.__players[player_id]
        player.charge_energy()
        taskMgr.do_method_later(0, lambda _: self.__connection_manager.send_bolt_pickup_trigger(bolt_id),
                                "send input on next frame")

    def setup_bolts(self, current_bolts):
        if self.__bolts_set_up:
            return
        self.__bolts_set_up = True
        self.__bolt_factory.undump_bolts(current_bolts)

    def update_bolts(self, old_bolt_id, new_bolt):
        self.__bolt_factory.remove_bolt(old_bolt_id)
        self.__bolt_factory.copy_bolts([new_bolt])

    def player_flag_pickup(self, player_id):
        player = self.__players[player_id]
        self.__flag.get_picked(player)

    def player_flag_drop(self, player_id):
        player = self.__players[player_id]
        self.__flag.get_dropped(player)

    def apply_local_diffs(self, server_game_state: GameStateDiff):
        """
        Applies diffs between the time when server had built
        the game state and the time data arrived locally
        """
        while len(self.__game_state_diffs) > 0:
            state = self.__game_state_diffs.popleft()
            if state.step.end < server_game_state.step.end:
                continue
            else:
                server_game_state.apply(state)
                while len(self.__game_state_diffs) > 0:
                    state = self.__game_state_diffs.popleft()
                    server_game_state.apply(state)
                break

    def update_positions_and_reconciliate(self, server_game_state: GameStateDiff):
        """
        Perform client side reconciliation
        and smooth out player movement using interpolation
        """
        for player in self.__players.values():
            if player is not self.__main_player:
                if player.get_id() not in server_game_state.player_state.keys():
                    continue
                player.replace_state(server_game_state.player_state[player.get_id()])
                player.sync_position()
            else:
                self.__main_player_server_view \
                    .replace_state(server_game_state.player_state[player.get_id()])
                self.__main_player_server_view.sync_position()
                self.__main_player.update_position()
                lerp = self.__main_player.state.motion_state \
                    .lerp(self.__lerp_factor, self.__main_player_server_view.state.motion_state)
                self.__main_player.state.motion_state.apply(lerp)
                self.__main_player.sync_position()

    def update_main_player_position(self):
        """
        Interpolate player positions when no server game state update arrived
        by moving both positions simultaneously and once again
        reducing the difference by given fraction (lerp)
        """
        last_player_position = self.__main_player.state.clone()
        self.__main_player.update_position()
        diff = last_player_position.diff(self.__main_player.state)
        self.__main_player_server_view.state.apply(diff)
        self.__main_player_server_view.sync_position()
        lerp = self.__main_player.state.motion_state \
            .lerp(self.__lerp_factor, self.__main_player_server_view.state.motion_state)
        self.__main_player.state.motion_state.apply(lerp)
        self.__main_player.sync_position()

    def interpolate_other_players_positions(self):
        """
        Show other players movement self.other_players_delay ms in the past
        """
        if len(self.__server_game_state_transfer_deque) == 0:
            return

        target_time = time.time() - self.__other_players_delay
        i = 0
        while i < len(self.__server_game_state_transfer_deque):
            if self.__server_game_state_transfer_deque[i].step.end < target_time:
                i += 1
            else:
                break
        else:
            # target_time is ahead of all known states - use the most recent
            state: PlayerStateDiff
            for id, state in self.__server_game_state_transfer_deque[-1].player_state.items():
                if id == self.__main_player.get_id():
                    continue
                self.__players[id].replace_state(state.clone())
                self.__players[id].sync_position()
            return

        # i-th state is our best guess
        # make a diff with prior one, cut it to target_time and apply
        if i <= 0:
            # prior state doesn't exist - we can't get diff - use what we have
            for id, state in self.__server_game_state_transfer_deque[i].player_state.items():
                if id == self.__main_player.get_id():
                    continue
                self.__players[id].replace_state(state.clone())
                self.__players[id].sync_position()
            return
        prior_state = self.__server_game_state_transfer_deque[i - 1].clone()
        diff = prior_state.diff(self.__server_game_state_transfer_deque[i])
        for id, state in diff.player_state.items():
            if id == self.__main_player.get_id():
                continue
            self.__players[id].replace_state(prior_state.player_state[id])
            lerp = state.motion_state.cut_end(target_time)
            self.__players[id].state.motion_state.apply(lerp)
            self.__players[id].sync_position()

    def game_state_snapshot(self, task):
        self.__game_state_diffs.append(
            self.__last_game_state.diff(self.__game_state)
        )
        return task.cont

    def queue_server_game_state(self, transfer: NetworkTransfer):
        server_game_state = GameStateDiff.empty(self.__game_state.player_state.keys())
        server_game_state.restore(transfer)
        for id, player_state in server_game_state.player_state.items():
            if id not in self.__players:
                self.setup_player(player_state)
        self.__server_game_state_transfer_deque.append(server_game_state)
        while len(self.__server_game_state_transfer_deque) > 5:
            self.__server_game_state_transfer_deque.popleft()
        self.__tick_update = True
        bullet_metadata = transfer.get("bullets").split(",")
        if len(bullet_metadata) > 1 or bullet_metadata[0] != "":
            self.__spawn_incoming_bullets(bullet_metadata, server_game_state.step.end)

    def __spawn_incoming_bullets(self, bullet_metadata: list[str], state_update_time: float):
        for data in bullet_metadata:
            bullet = self.__bullet_factory.get_one_from_metadata(tuple(map(float, data.split(" "))))  # type: ignore
            bullet.update_position_by_dt(time.time() - state_update_time - self.__other_players_delay)
            self.__bullets.append(bullet)

    def setup_map(self, tiles, map_size, season):
        self.__game.add_colliders_from(self.__flag)
        for bullet in self.__bullet_factory.bullets:
            self.__game.add_colliders_from(bullet)

        self.__game.setup_map(tiles, map_size, season)
        self.__game.update_collision_system()

        def update_camera(task):
            if self.__main_player is None:
                return task.cont
            self.__game.set_camera_pos(self.__main_player.model.getX(), self.__main_player.model.getY() - 10, 15)
            self.__game.set_camera_look_at(self.__main_player.model)
            return task.cont

        taskMgr.add(update_camera, "update camera")
