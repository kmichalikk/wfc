import panda3d.core as p3d
from panda3d.core import CollisionBox, Point3, CollisionSphere


def create_new_tile(loader: p3d.Loader, name: str, position: tuple, heading: int):
    node_path = loader.load_model(
        "assets/models/{}".format(name if name[-3:] == "glb" else (name + ".glb"))
    )
    node_path.set_pos(*position)
    node_path.set_h(heading)

    return node_path


collision_shapes = {
    "wall_slim_single_1": [CollisionBox(Point3(0, 0, 0.5), 0.5, 0.5, 1)],
    "wall_concave_1": [CollisionBox(Point3(-0.5, 0.5, 0.5), 0.5, 0.5, 1)],
    "wall_convex_1": [CollisionBox(Point3(-0.5, 0, 0.5), 0.5, 1, 1),
                      CollisionBox(Point3(0, 0.5, 0.5), 1, 0.5, 1)],
    "wall_slim_extend_1": [CollisionBox(Point3(0, 0, 0.5), 1, 0.5, 1)],
    "wall_slim_join2_1": [CollisionBox(Point3(-0.25, 0, 0.5), 0.75, 0.5, 1),
                          CollisionBox(Point3(0, -0.25, 0.5), 0.5, 0.75, 1)],
    "wall_slim_join3_1": [CollisionBox(Point3(0, 0, 0.5), 1, 0.5, 1),
                          CollisionBox(Point3(0, -0.25, 0.5), 0.5, 0.75, 1)],
    "wall_slim_join4_1": [CollisionBox(Point3(0, 0, 0.5), 1, 0.5, 1),
                          CollisionBox(Point3(0, 0, 0.5), 0.5, 1, 1)],
    "wall_slim_tip_1": [CollisionBox(Point3(0, 0.5, 0.5), 0.5, 0.5, 1)],
    "wall_straight_1_1": [CollisionBox(Point3(0, 0.5, 0.5), 1, 0.5, 1)],
    "wall_straight_2_1": [CollisionBox(Point3(0, 0.5, 0.5), 1, 0.5, 1)],
    "wall_straight_join1_1": [CollisionBox(Point3(0, 0.5, 0.5), 1, 0.5, 1),
                              CollisionBox(Point3(0, 0, 0.5), 0.5, 1, 1)],
    "plants_1": [CollisionBox(Point3(-0.6, 0.3, 0.5), 0.1, 0.1, 0.5),
                 CollisionSphere(0.15, 0.25, 0.2, 0.2),
                 CollisionSphere(-0.4, -0.75, 0.2, 0.2)],
    "empty_1": [],
    "water_concave_1": [],
    "water_convex_1": [],
    "water_extend_1": [],
    "water_full_1": []
}
