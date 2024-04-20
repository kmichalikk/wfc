import panda3d.core as p3d
from panda3d.core import NodePath

from common.collision.collision_object import CollisionObject
from common.collision.safe_space import SafeSpace
from common.tiles.tile_controller import create_new_tile, collision_shapes


def setup_collisions(game, tiles, map_size, bullet_factory):
    game.cTrav = p3d.CollisionTraverser()
    game.pusher = p3d.CollisionHandlerPusher()
    game.pusher.setHorizontal(True)
    game.collision_event_generator = p3d.CollisionHandlerEvent()
    game.collision_event_generator.add_in_pattern('%fn-into-%in')

    for bullet in bullet_factory.bullets:
        game.cTrav.add_collider(bullet.colliders[0], game.collision_event_generator)

    game.tile_colliders = []

    game.safe_spaces = []
    for i in range(4):
        game.safe_spaces.append(SafeSpace(game.render, i, map_size))

    tiles_parent = NodePath("tiles")
    tile: p3d.NodePath
    for tile_data in tiles:
        tile = create_new_tile(game.loader, tile_data["node_path"], tile_data["pos"], tile_data["heading"])
        tile.reparent_to(tiles_parent)
        game.tile_colliders.append(
            CollisionObject(
                tile,
                "wall" if "wall" in tile_data["node_path"] else tile_data["node_path"],
                collision_shapes[tile_data["node_path"]]
            )
        )

    tiles_parent.flatten_strong()
    tiles_parent.reparent_to(game.render)

    for space in game.safe_spaces:
        space.show()
