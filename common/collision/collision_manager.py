import panda3d.core as p3d
from panda3d.core import NodePath
from common.collision.collision_object import CollisionObject
from common.collision.safe_space import SafeSpace
from common.tiles.tile_controller import create_new_tile, get_collision_shapes


class CollisionManager:
    def __init__(self, render, loader, flag_collider, bullet_factory):
        self.render = render
        self.loader = loader
        self.flag_collider = flag_collider
        self.bullet_factory = bullet_factory
        self.cTrav = p3d.CollisionTraverser()
        self.pusher = p3d.CollisionHandlerPusher()
        self.pusher.setHorizontal(True)
        self.pusher.add_in_pattern('%fn-into-%in')
        self.tile_colliders = []
        self.safe_spaces = []

    def setup_collisions(self, tiles, map_size, season):
        self.setup_traverser()
        self.setup_safe_spaces(map_size)
        self.setup_tile_colliders(tiles, season)
        return self.cTrav, self.pusher

    def setup_traverser(self):
        self.cTrav.add_collider(self.flag_collider, self.pusher)
        for bullet in self.bullet_factory.bullets:
            self.cTrav.add_collider(bullet.colliders[0], self.pusher)

    def setup_safe_spaces(self, map_size):
        for i in range(4):
            self.safe_spaces.append(SafeSpace(self.render, i, map_size, self.loader))

    def setup_tile_colliders(self, tiles, season):
        tiles_parent = NodePath("tiles")
        for tile_data in tiles:
            tile = create_new_tile(self.loader, tile_data["node_path"], tile_data["pos"], tile_data["heading"], season)
            tile.reparent_to(tiles_parent)
            self.tile_colliders.append(
                CollisionObject(
                    tile,
                    "wall" if "wall" in tile_data["node_path"] else tile_data["node_path"],
                    get_collision_shapes(tile_data["node_path"])
                )
            )
        tiles_parent.flatten_strong()
        tiles_parent.reparent_to(self.render)

    def setup_player_collision(self, player_collider, view=0):
        self.cTrav.add_collider(player_collider, self.pusher)
        self.pusher.add_collider(player_collider, player_collider)
        if view:
            player_collider.show()

    def get_tile_colliders(self):
        return self.tile_colliders
