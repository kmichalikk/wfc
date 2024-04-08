from panda3d.core import CollisionSphere, Vec3
from common.collision.collision_object import CollisionObject


class Flag(CollisionObject):
    def __init__(self, loader, player=None):
        self.player = player
        self.position = Vec3(8, 8, 0)
        self.model = loader.load_model("../common/assets/models/flag.glb")

        collision_spheres = [CollisionSphere(0, 0, 0.5, 0.2)]

        super().__init__(self.model, "flag", collision_spheres)