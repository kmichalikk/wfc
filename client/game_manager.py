import time
from collections import deque
from queue import Queue

import panda3d.core as p3d

from typing import Union
from direct.showbase import ShowBase
from direct.task import Task

from common.collision.setup import setup_collisions
from common.state.game_state_diff import GameStateDiff
from common.state.player_state_diff import PlayerStateDiff
from common.tiles.tile_controller import create_new_tile
from common.player.player_controller import PlayerController
from common.tiles.tile_node_path_factory import TileNodePathFactory
from common.transfer.network_transfer import NetworkTransfer
from common.typings import TimeStep


class GameManager:
    def __init__(self, game: ShowBase, node_path_factory: TileNodePathFactory):
        self.players: dict[str, PlayerController] = {}
        self.main_player: Union[None, PlayerController] = None
        self.main_player_server_view: Union[None, PlayerController] = None
        self.game_state_diffs: deque[GameStateDiff] = deque()
        self.last_game_state: GameStateDiff = GameStateDiff(TimeStep(begin=0, end=time.time() - 0.2))
        self.game_state: GameStateDiff = GameStateDiff(TimeStep(begin=0, end=time.time() - 0.1))
        self.server_game_state_transfer_queue: Queue[NetworkTransfer] = Queue()
        self.game = game
        self.node_path_factory = node_path_factory
        self.sync_tasks: dict[str, Task] = {}

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

        return player

    def set_main_player(self, player: PlayerController):
        self.main_player = player
        self.game.taskMgr.add(self.sync_game_state, "update players positions", sort=1)
        self.game.taskMgr.add(self.game_state_snapshot, "store game state history up to .5 sec", sort=2)

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
        game_state_transfer = None
        while not self.server_game_state_transfer_queue.empty():
            game_state_transfer = self.server_game_state_transfer_queue.get()

        self.last_game_state = self.game_state.clone()
        if game_state_transfer is not None:
            self.update_positions_and_reconciliate(game_state_transfer)
        else:
            self.update_positions()

        return task.cont

    def update_positions_and_reconciliate(self, transfer: NetworkTransfer):
        server_game_state = GameStateDiff.empty(self.game_state.player_state.keys())
        server_game_state.restore(transfer)
        # print("[DIFF] Server state at {} vs now {}, history len = {}".format(
        #     server_game_state.step.end, time.time(), len(self.game_state_diffs)))
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
                    .lerp(0.1, self.main_player_server_view.state.motion_state)
                if lerp.position.length() > 0.001:
                    self.main_player.state.motion_state.apply(lerp)

    def update_positions(self):
        last_player_position = self.main_player.state.clone()
        self.main_player.update_position()
        diff = last_player_position.diff(self.main_player.state)
        self.main_player_server_view.state.apply(diff)
        self.main_player_server_view.sync_position()
        lerp = self.main_player.state.motion_state \
            .lerp(0.1, self.main_player_server_view.state.motion_state)

        if lerp.position.length() > 0.001:
            self.main_player.state.motion_state.apply(lerp)

        for player in self.players.values():
            player.sync_position()

    def game_state_snapshot(self, task):
        self.game_state_diffs.append(
            self.last_game_state.diff(self.game_state)
        )
        return task.cont

    def queue_server_game_state(self, transfer: NetworkTransfer):
        self.server_game_state_transfer_queue.put(transfer)

    def setup_map(self, game, tiles, map_size):
        game.disableMouse()

        properties = p3d.WindowProperties()
        properties.set_size(1280, 800)
        game.win.request_properties(properties)

        point_light_node = game.render.attach_new_node(p3d.PointLight("light"))
        point_light_node.set_pos(0, -10, 10)
        game.render.set_light(point_light_node)

        setup_collisions(game, tiles, map_size)

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
