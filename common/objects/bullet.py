from direct.showbase.ShowBaseGlobal import globalClock

from common.collision.collision_object import CollisionObject
import panda3d.core as p3d

from common.typings import BulletMetadata
from common.typings import SupportsCollisionRegistration


class Bullet(CollisionObject, SupportsCollisionRegistration):
    def __init__(self, parent: p3d.NodePath, position: p3d.Vec3, direction: p3d.Vec3, owner_id: str, bullet_id: int,
                 timestamp: int):
        collision_sphere = p3d.CollisionSphere(0, 0, 0, 0.15)
        collision_sphere.set_tangible(False)
        super().__init__(parent, 'bullet', [collision_sphere])

        self.colliders[0].set_pos(position)
        self.colliders[0].show()
        self.colliders[0].set_tag('id', str(bullet_id))
        self.owner_id: str = owner_id
        self.bullet_id: int = bullet_id
        self.timestamp: int = timestamp
        self.position = position
        self.direction = direction.normalized()
        self.velocity = 15

    def update_position(self):
        dt = globalClock.get_dt()
        self.update_position_by_dt(dt)

    def get_metadata(self) -> BulletMetadata:
        return (
            self.position.get_x(), self.position.get_y(),
            self.direction.get_x(), self.direction.get_y()
        )

    def update_position_by_dt(self, dt):
        self.position.set_x(self.position.get_x() + self.direction.get_x() * self.velocity * dt)
        self.position.set_y(self.position.get_y() + self.direction.get_y() * self.velocity * dt)
        self.colliders[0].set_pos(self.position)

    def get_colliders(self) -> list[CollisionObject]:
        return self.colliders
