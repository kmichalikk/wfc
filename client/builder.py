import panda3d.core as p3d
from panda3d.core import CollisionTraverser, CollisionHandlerPusher
from common.collision.border import Border
from common.collision.collision_object import CollisionObject
from common.state.player_state_diff import PlayerStateDiff
from common.tiles.tile_controller import create_new_tile, collision_shapes
from common.tiles.tile_node_path_factory import TileNodePathFactory
from common.player.player_controller import PlayerController
from common.typings import TimeStep


def setup_map(game, tiles):
    game.disableMouse()

    properties = p3d.WindowProperties()
    properties.set_size(1280, 800)
    game.win.request_properties(properties)

    point_light_node = game.render.attach_new_node(p3d.PointLight("light"))
    point_light_node.set_pos(0, -10, 10)
    game.render.set_light(point_light_node)

    game.cTrav = CollisionTraverser()
    game.pusher = CollisionHandlerPusher()
    game.pusher.setHorizontal(True)

    game.border = Border(game.render, game.map_size)
    game.tile_colliders = []

    tile: p3d.NodePath
    for tile_data in tiles:
        tile = create_new_tile(game.loader, tile_data["node_path"], tile_data["pos"], tile_data["heading"])
        tile.reparent_to(game.render)
        game.tile_colliders.append(CollisionObject(tile, tile_data["node_path"],
                                                   collision_shapes[tile_data["node_path"]]))

    game.taskMgr.add(game.update_camera, "update camera")


def setup_player(game, player_positions):
    node_path_factory = TileNodePathFactory(game.loader)
    player_node_path = node_path_factory.get_player_model()
    player_node_path.set_pos(player_positions[0])
    player_node_path.reparent_to(game.render)

    game.player = PlayerController(
        player_node_path,
        PlayerStateDiff(TimeStep(0, 0, 0), "0")
    )
    game.attach_input()
    game.player_movement_task = game.taskMgr.add(game.player.update_position, "update player position")
