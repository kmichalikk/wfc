from panda3d.core import NodePath, Vec3, BitMask32, CollisionNode, CollisionCapsule
from panda3d.core import CollisionTraverser, CollisionHandlerPusher
from src.player.motion import Motion


class Player:
    def __init__(self, model: NodePath):
        self.model = model
        self.motion = Motion(model.get_pos())

        collider_node = CollisionNode("player")
        collider_node.add_solid(CollisionCapsule(0, 0, 0, 0, 0, 0.6, 0.2))
        self.collider = self.model.attach_new_node(collider_node)

    def update_position(self, task):
        self.motion.update()
        self.model.set_pos(self.motion.position)
        if self.motion.velocity.length() > 0.01:
            self.model.set_h(-self.motion.velocity.normalized().signed_angle_deg(Vec3(0, 1, 0), Vec3(0, 0, 1)))
        return task.cont