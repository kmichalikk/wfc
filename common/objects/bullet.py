from direct.showbase.ShowBaseGlobal import globalClock

from common.collision.collision_object import CollisionObject
import panda3d.core as p3d


class Bullet(CollisionObject):
    def __init__(self, parent: p3d.NodePath, position: p3d.Vec3, direction: p3d.Vec3, owner_id: str):
        super().__init__(parent, 'bullet', [p3d.CollisionSphere(0, 0, 0, 0.1)])
        self.colliders[0].set_pos(position)
        self.colliders[0].show()
        print(self.colliders[0].get_pos())
        self.owner_id: str = owner_id
        self.position = position
        self.direction = direction.normalized()
        self.velocity = 10

    def update_position(self):
        dt = globalClock.get_dt()
        self.position.set_x(self.position.get_x() + self.direction.get_x() * self.velocity * dt)
        self.position.set_y(self.position.get_y() + self.direction.get_y() * self.velocity * dt)
        self.colliders[0].set_pos(self.position)
