from panda3d.core import CollisionTube
from common.collision.collision_object import CollisionObject


class Border(CollisionObject):
    def __init__(self, render, map_size):

        collision_tubes = [
            CollisionTube(-2, -2, 0, map_size * 2, -2, 0, 1),
            CollisionTube(-2, map_size * 2, 0, map_size * 2, map_size * 2, 0, 1),
            CollisionTube(-2, -2, 0, -2, map_size * 2, 0, 1),
            CollisionTube(map_size * 2, -2, 0, map_size * 2, map_size * 2, 0, 1)
        ]

        super().__init__(render, "border", collision_tubes)
