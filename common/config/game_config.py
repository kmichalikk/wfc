import pickle

from panda3d.core import Vec3

from common.state.player_state_diff import PlayerStateDiff
from common.typings import SupportsNetworkTransfer, SupportsBuildingNetworkTransfer


class GameConfig(SupportsNetworkTransfer):
    def __init__(self, tiles, id: str, states: list[PlayerStateDiff]):
        self.tiles = tiles
        self.id = id
        self.all_ids = []
        self.player_states = states

    def transfer(self, builder: SupportsBuildingNetworkTransfer):
        builder.add("gctiles", pickle.dumps(self.tiles).hex())
        builder.add("id", self.id)
        builder.add("ids", ",".join([state.id for state in self.player_states]))
        for state in self.player_states:
            state.transfer(builder)

    def restore(self, transfer):
        self.tiles = pickle.loads(bytes.fromhex(transfer.get("gctiles")))
        self.all_ids = transfer.get("ids").split(",")
        self.id = transfer.get("id")
        for id in self.all_ids:
            state = PlayerStateDiff.empty(id)
            state.restore(transfer)
            self.player_states.append(state)

    @classmethod
    def empty(cls):
        return cls([], "0", [])
