import pickle

from panda3d.core import Vec3

from common.typings import SupportsNetworkTransfer, SupportsBuildingNetworkTransfer


class GameConfig(SupportsNetworkTransfer):
    def __init__(self, tiles, player_position: Vec3):
        self.tiles = tiles
        self.player_position = player_position

    def transfer(self, builder: SupportsBuildingNetworkTransfer):
        builder.add("gctiles", pickle.dumps(self.tiles).hex())
        builder.add("gcx", str(self.player_position.get_x()))
        builder.add("gcy", str(self.player_position.get_y()))

    def restore(self, transfer):
        self.tiles = pickle.loads(bytes.fromhex(transfer.get("gctiles")))
        self.player_position.set_x(float(transfer.get("gcx")))
        self.player_position.set_y(float(transfer.get("gcy")))
