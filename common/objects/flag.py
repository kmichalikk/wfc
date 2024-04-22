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

        super().__init__(self.model, "flag", collision_spheres)

    def taken(self):
        return bool(self.player)


