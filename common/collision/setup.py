import panda3d.core as p3d
from panda3d.core import NodePath

from common.collision.safe_space import SafeSpace
from common.collision.collision_object import CollisionObject
from common.tiles.tile_controller import create_new_tile, collision_shapes, water_borders
from common.tiles.flag import Flag


def setup_collisions(game, tiles, map_size):
    game.cTrav = p3d.CollisionTraverser()
    game.pusher = p3d.CollisionHandlerPusher()
    game.pusher.setHorizontal(True)

    game.pusher.addInPattern('%fn-into-%in')
    game.pusher.addOutPattern('%fn-outof-%in')


    game.safe_spaces = []
    for i in range(4):
        game.safe_spaces.append(SafeSpace(game.render, i, map_size))
    game.tile_colliders = []
    tiles_parent = NodePath("tiles")
    tile: p3d.NodePath
    for tile_data in tiles:
        tile = create_new_tile(game.loader, tile_data["node_path"], tile_data["pos"], tile_data["heading"])
        tile.reparent_to(tiles_parent)

        if "water" in tile_data["node_path"]:
            game.tile_colliders.append(CollisionObject(tile, "water",
                                                       collision_shapes[tile_data["node_path"]]))
            game.tile_colliders.append(CollisionObject(tile, "grass",
                                                       water_borders[tile_data["node_path"]]))
        else:
            game.tile_colliders.append(CollisionObject(tile, tile_data["node_path"],
                                                       collision_shapes[tile_data["node_path"]]))

    game.flag = Flag(game.loader)
    game.flag.model.reparentTo(game.render)
    game.flag.model.setPos(map_size-2, map_size-2, 0)

    for space in game.safe_spaces:
        space.show()

    tiles_parent.flatten_strong()
    tiles_parent.reparent_to(game.render)
