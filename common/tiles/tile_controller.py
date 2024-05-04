import panda3d.core as p3d
from panda3d.core import CollisionBox, Point3, CollisionSphere, CollisionCapsule


def create_new_tile(loader: p3d.Loader, name: str, position: tuple, heading: int, season: int):
    season_folder = "summer" if season == 0 else "winter"
    node_path = loader.load_model(
        f"../common/assets/models/{season_folder}/{name if name[-3:] == 'glb' else (name + '.glb')}"
    )
    node_path.set_pos(*position)
    node_path.set_h(heading)

    return node_path


collision_shapes = {
    "wall_slim_single_1": [CollisionSphere(0, 0, 0.5, 0.7)],
    "wall_concave_1": [CollisionBox(Point3(-0.5, 0.75, 0.5), 0.5, 0.25, 1),
                       CollisionBox(Point3(-0.75, 0.5, 0.5), 0.25, 0.5, 1),
                       CollisionSphere(-0.5, 0.5, 0.5, 0.5)],
    "wall_convex_1": [CollisionBox(Point3(-0.5, 0, 0.5), 0.5, 1, 1),
                      CollisionBox(Point3(0, 0.5, 0.5), 1, 0.5, 1),
                      CollisionCapsule(-0.4, -0.6, 0.5, 0.6, 0.4, 0.5, 0.5)],
    "wall_slim_extend_1": [CollisionBox(Point3(0, 0, 0.5), 1, 0.5, 1)],
    "wall_slim_join2_1": [CollisionBox(Point3(-0.5, 0, 0.5), 0.5, 0.5, 1),
                          CollisionBox(Point3(0, -0.5, 0.5), 0.5, 0.5, 1),
                          CollisionSphere(0.1, 0.1, 0.5, 0.5)],
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
    "full_1": [CollisionBox(Point3(0, 0, 0.5), 1, 1, 1)],
    "water_concave_1": [],
    "water_convex_1": [],
    "water_extend_1": [],
    "water_full_1": [],

    "empty_1": []
}

water_borders = {
    "water_concave_1": [CollisionBox(Point3(-0.65, 0.65, 0.5), 0.35, 0.35, 0.5)],
    "water_convex_1": [CollisionBox(Point3(-0.65, 0, 0.5), 0.35, 1, 0.5),
                       CollisionBox(Point3(0, 0.65, 0.5), 1, 0.35, 0.5)],
    "water_extend_1": [CollisionBox(Point3(0, 0.65, 0.5), 1, 0.35, 0.5)],
    "water_full_1": []
}
