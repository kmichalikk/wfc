import pickle

from panda3d.core import Vec3

from common.state.player_state_diff import PlayerStateDiff
from common.typings import SupportsNetworkTransfer, SupportsBuildingNetworkTransfer


class GameConfig(SupportsNetworkTransfer):
    def __init__(self, tiles, player_state: PlayerStateDiff):
        self.tiles = tiles
        self.player_state = player_state

    def transfer(self, builder: SupportsBuildingNetworkTransfer):
        builder.add("gctiles", pickle.dumps(self.tiles).hex())
        self.player_state.transfer(builder)

    def restore(self, transfer):
        self.tiles = pickle.loads(bytes.fromhex(transfer.get("gctiles")))
        self.player_state.restore(transfer)
