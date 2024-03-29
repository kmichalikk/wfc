from panda3d.core import NodePath, Vec3, CollisionSphere
from common.player.motion import Motion
from common.collision.collision_object import CollisionObject


class PlayerController(CollisionObject):
    def __init__(self, model: NodePath):
        super().__init__(parent=model.parent, name="player", shapes=[CollisionSphere(0, 0, 0.5, 0.25)])

        self.model = model
        self.motion = Motion(model.get_pos())

    def update_position(self, task):
        self.motion.position = self.colliders[0].get_pos()
        self.motion.update()
        self.colliders[0].set_pos(self.motion.position)
        self.model.set_pos(self.colliders[0].get_pos())
        if self.motion.velocity.length() > 0.01:
            self.model.set_h(-self.motion.velocity.normalized().signed_angle_deg(Vec3(0, 1, 0), Vec3(0, 0, 1)))
        return task.cont
