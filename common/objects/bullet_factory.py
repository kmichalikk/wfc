import time
import panda3d.core as p3d

from common.objects.bullet import Bullet
from common.typings import BulletMetadata


class BulletFactory:
    """
    Only few bullets appear on screen at the same time. BulletFactory manages set count of bullets
    and circulates between them. Bullets must be destroyed by 'destroy' method in order to be reused.
    """
    COUNT = 100

    def __init__(self, render):
        self.bullets = []
        for i in range(self.COUNT):
            bullet = Bullet(render, p3d.Vec3(-10, i, 0), p3d.Vec3.zero(), "", i, int(time.time()*1000))
            self.bullets.append(bullet)

        self.id = 0

    def register_colliders(self, pusher):
        for bullet in self.bullets:
            pusher.add_collider(bullet)
        return [b.collision_node for b in self.bullets]

    def get_one(self, position, direction, owner_id):
        bullet = self.bullets[self.id]
        self.id = (self.id + 1) % self.COUNT
        bullet.position = position
        bullet.direction = direction
        bullet.owner_id = owner_id
        return bullet

    def get_one_from_metadata(self, metadata: BulletMetadata):
        return self.get_one(
            p3d.Vec3(metadata[0], metadata[1], 0.5),
            p3d.Vec3(metadata[2], metadata[3], 0),
            ""
        )

    def destroy(self, bullet_id):
        self.bullets[bullet_id].position = p3d.Vec3(-10, bullet_id, 0)
        self.bullets[bullet_id].direction = p3d.Vec3.zero()
        self.bullets[bullet_id].owner_id = ""
