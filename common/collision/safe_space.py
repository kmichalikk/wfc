import panda3d.core as p3d
from common.collision.collision_object import CollisionObject


class SafeSpace(CollisionObject):
    def __init__(self, render, i, map_size, loader):

        collision_spheres = [
            [p3d.CollisionSphere(4, 4, 0, 1)],
            [p3d.CollisionSphere(4, (map_size - 3) * 2, 0, 1)],
            [p3d.CollisionSphere((map_size - 3) * 2, 4, 0, 1)],
            [p3d.CollisionSphere((map_size - 3) * 2, (map_size - 3) * 2, 0, 1)]
        ]

        node_path = loader.load_model("../common/assets/models/safe_space.glb")
        node_path.reparent_to(render)
        node_path.set_pos(collision_spheres[i][0].get_center())
        collision_spheres[i][0].set_tangible(False)

        super().__init__(render, "safe_space"+str(i), collision_spheres[i])
