import pickle
import zlib

from common.state.player_state_diff import PlayerStateDiff
from common.typings import SupportsNetworkTransfer, SupportsBuildingNetworkTransfer


class GameConfig(SupportsNetworkTransfer):
    def __init__(self, tiles, expected_players, id: str, states: list[PlayerStateDiff], size: int, season: int):
        self.tiles = tiles
        self.id = id
        self.expected_players = expected_players
        self.all_ids = []
        self.player_states = states
        self.size = size
        self.season = season

    def transfer(self, builder: SupportsBuildingNetworkTransfer):
        builder.add("gctiles", zlib.compress(pickle.dumps(self.tiles)).hex())
        builder.add("id", self.id)
        builder.add("size", self.size)
        builder.add("expected_players", self.expected_players)
        builder.add("season", self.season)
        builder.add("ids", ",".join([state.id for state in self.player_states]))
        for state in self.player_states:
            state.transfer(builder)

    def restore(self, transfer):
        self.tiles = pickle.loads(zlib.decompress(bytes.fromhex(transfer.get("gctiles"))))
        self.all_ids = transfer.get("ids").split(",")
        self.id = transfer.get("id")
        self.size = transfer.get("size")
        self.expected_players = transfer.get("expected_players")
        self.season = transfer.get("season")
        for id in self.all_ids:
            state = PlayerStateDiff.empty(id)
            state.restore(transfer)
            self.player_states.append(state)

    @classmethod
    def empty(cls):
        return cls([], 0, "0", [], 10, 0)
