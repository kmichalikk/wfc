import panda3d.core as p3d
from panda3d.core import NodePath

from common.collision.border import Border
from common.collision.collision_object import CollisionObject
from common.tiles.tile_controller import create_new_tile, collision_shapes


def setup_collisions(game, tiles, map_size):
    game.cTrav = p3d.CollisionTraverser()
    game.pusher = p3d.CollisionHandlerPusher()
    game.pusher.setHorizontal(True)

    game.border = Border(game.render, map_size)
    game.tile_colliders = []

    tiles_parent = NodePath("tiles")
    tile: p3d.NodePath
    for tile_data in tiles:
        tile = create_new_tile(game.loader, tile_data["node_path"], tile_data["pos"], tile_data["heading"])
        tile.reparent_to(tiles_parent)
        game.tile_colliders.append(CollisionObject(tile, tile_data["node_path"],
                                                   collision_shapes[tile_data["node_path"]]))
    tiles_parent.flatten_strong()
    tiles_parent.reparent_to(game.render)
