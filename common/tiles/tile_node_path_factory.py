import panda3d.core as p3d


class TileNodePathFactory:
    def __init__(self, loader: p3d.Loader):
        self.loader = loader

    def get_player_model(self, player_id):
        return self.loader.load_model(f"../common/assets/models/players/player{player_id}.glb")
