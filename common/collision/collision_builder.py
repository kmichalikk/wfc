import panda3d.core as p3d
from panda3d.core import NodePath
from common.collision.collision_object import CollisionObject
from common.collision.safe_space import SafeSpace
from common.tiles.tile_controller import create_new_tile, get_collision_shapes
from common.typings import SupportsCollisionRegistration


class CollisionBuilder:
    def __init__(self, render, loader):
        self.render = render
        self.loader = loader
        self.cTrav = p3d.CollisionTraverser()
        self.pusher = p3d.CollisionHandlerPusher()
        self.pusher.setHorizontal(True)
        self.pusher.add_in_pattern('%fn-into-%in')
        self.__tile_colliders = []
        self.__safe_spaces = []

    def get_collision_system(self):
        return self.cTrav, self.pusher

    def add_safe_spaces(self, map_size):
        for i in range(4):
            self.__safe_spaces.append(SafeSpace(self.render, i, map_size, self.loader))

    def add_tile_colliders(self, tiles, season):
        tiles_parent = NodePath("tiles")
        for tile_data in tiles:
            tile = create_new_tile(self.loader, tile_data["node_path"], tile_data["pos"], tile_data["heading"], season)
            tile.reparent_to(tiles_parent)
            self.__tile_colliders.append(
                CollisionObject(
                    tile,
                    "wall" if "wall" in tile_data["node_path"] else tile_data["node_path"],
                    get_collision_shapes(tile_data["node_path"])
                )
            )
        tiles_parent.flatten_strong()
        tiles_parent.reparent_to(self.render)

    def add_colliders_from(self, obj: SupportsCollisionRegistration, view=False):
        for collider in obj.get_colliders():
            self.cTrav.add_collider(collider, self.pusher)
            self.pusher.add_collider(collider, collider)
            if view:
                collider.show()

    def get_tile_colliders(self):
        return self.__tile_colliders
