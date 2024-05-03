from panda3d.core import CollisionSphere
from common.collision.collision_object import CollisionObject


class SafeSpace(CollisionObject):
    def __init__(self, render, i, map_size):

        collision_spheres = [
            [CollisionSphere(4, 4, 0, 1)],
            [CollisionSphere(4, (map_size - 3) * 2, 0, 1)],
            [CollisionSphere((map_size - 3) * 2, 4, 0, 1)],
            [CollisionSphere((map_size - 3) * 2, (map_size - 3) * 2, 0, 1)]
        ]

        super().__init__(render, "safe_space"+str(i), collision_spheres[i])
