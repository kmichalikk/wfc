import panda3d.core as p3d

from typing import Union
from direct.showbase import ShowBase
from direct.task import Task

from common.collision.setup import setup_collisions
from common.state.game_state_diff import GameStateDiff
from common.state.player_state_diff import PlayerStateDiff
from common.tiles.tile_controller import create_new_tile
from common.tiles.tile_node_path_factory import TileNodePathFactory
from common.player.player_controller import PlayerController
from common.transfer.network_transfer import NetworkTransfer


class GameManager:
    def __init__(self):
        self.players: dict[str, PlayerController] = {}
        self.main_player: Union[None, PlayerController] = None
        self.game_state: GameStateDiff = GameStateDiff.empty()
        self.sync_tasks: dict[str, Task] = {}

    def setup_player(self, game: ShowBase, player_state: PlayerStateDiff, main_player=False):
        node_path_factory = TileNodePathFactory(game.loader)
        player_node_path = node_path_factory.get_player_model()
        player_node_path.set_pos(player_state.get_position())
        player_node_path.reparent_to(game.render)

        player = PlayerController(
            player_node_path,
            player_state
        )
        self.game_state.player_state[player_state.id] = player_state
        self.players[player_state.id] = player

        if main_player:
            game.attach_input()
            self.main_player = player
            self.sync_tasks[player_state.id] = game.taskMgr.add(player.update_position, "update player position")
            player_collider = player.colliders[0]
            game.cTrav.addCollider(player_collider, game.pusher)
            game.pusher.addCollider(player_collider, player_collider)
        else:
            self.sync_tasks[player_state.id] = game.taskMgr.add(player.sync_position, "sync player position")

    def sync_game_state(self, game_state_transfer: NetworkTransfer):
        self.game_state.restore(game_state_transfer)
        for player in self.players.values():
            player.state.restore(game_state_transfer)

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
