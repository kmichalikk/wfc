import panda3d.core as p3d


class TileNodePathFactory:
    def __init__(self, loader: p3d.Loader):
        self.loader = loader

    def get_tile_node_path(self, name: str) -> p3d.NodePath:
        return self.loader.load_model(
            "assets/models/{}".format(name if name[-3:] == "glb" else (name + ".glb"))
        )
