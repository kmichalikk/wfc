from direct.showbase.ShowBaseGlobal import globalClock

from common.collision.collision_object import CollisionObject
import panda3d.core as p3d


class Bullet(CollisionObject):
    def __init__(self, parent: p3d.NodePath, position: p3d.Vec3, direction: p3d.Vec3, owner_id: str, bullet_id: int,
                 timestamp: int):
        super().__init__(parent, 'bullet', [p3d.CollisionSphere(0, 0, 0, 0.1)])
        self.colliders[0].set_pos(position)
        self.colliders[0].show()
        self.colliders[0].set_tag('id', str(bullet_id))
        self.owner_id: str = owner_id
        self.bullet_id: int = bullet_id
        self.timestamp: int = timestamp
        self.position = position
        self.direction = direction.normalized()
        self.velocity = 10

    def update_position(self):
        dt = globalClock.get_dt()
        self.update_position_by_dt(dt)

    def update_position_by_dt(self, dt):
        self.position.set_x(self.position.get_x() + self.direction.get_x() * self.velocity * dt)
        self.position.set_y(self.position.get_y() + self.direction.get_y() * self.velocity * dt)
        self.colliders[0].set_pos(self.position)
