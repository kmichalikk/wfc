from panda3d.core import CollisionSphere

from common.collision.collision_object import CollisionObject


class Bolt(CollisionObject):
    def __init__(self, loader, render, position, id: str):
        self.id = id
        self.position = position
        self.model = loader.load_model("../common/assets/models/bolt.glb")
        self.model.setPos(self.position)
        self.model.setHpr(90, 0, 0)
        self.model.reparentTo(render)

        collision_spheres = [CollisionSphere(0, 0, 0.5, 0.2)]
        collision_spheres[0].set_tangible(False)

        super().__init__(self.model, "bolt" + id, collision_spheres)

    def remove(self):
        self.model.detachNode()
        self.colliders[0].detachNode()

