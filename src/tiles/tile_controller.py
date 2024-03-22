import panda3d.core as p3d
from panda3d.core import CollisionNode, CollisionBox, Point3


def create_new_tile(loader: p3d.Loader, name: str, position: tuple, heading: int):
    node_path = loader.load_model(
        "assets/models/{}".format(name if name[-3:] == "glb" else (name + ".glb"))
    )
    node_path.set_pos(*position)
    node_path.set_h(heading)

    return node_path
