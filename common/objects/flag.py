from panda3d.core import Vec3, CollisionSphere

from common.collision.collision_object import CollisionObject
from common.config import MAP_SIZE


class Flag(CollisionObject):
    def __init__(self, game, player=None):
        self.player = player
        self.position = Vec3(MAP_SIZE - 2, MAP_SIZE - 2, 0)
        self.model = game.loader.load_model("../common/assets/models/flag.glb")
        self.model.setPos(self.position)
        self.model.reparentTo(game.render)

        collision_spheres = [CollisionSphere(0, 0, 0.5, 0.2)]
        collision_spheres[0].set_tangible(False)

        super().__init__(self.model, "flag", collision_spheres)

    def taken(self):
        return bool(self.player)

    def get_picked(self, player):
        self.player = player
        self.model.wrtReparentTo(player.model)
        self.model.setPos(Vec3(0, 0, 1))
        player.state.pickup_flag()

    def get_dropped(self, player):
        self.player = None
        self.model.wrtReparentTo(player.model.parent)
        self.model.setPos(player.model, 1, 1, 0)
        player.state.drop_flag()
