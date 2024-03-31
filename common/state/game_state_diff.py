from common.state.player_state_diff import PlayerStateDiff
from common.typings import SupportsDiff, SupportsNetworkTransfer, TimeStep, SupportsBuildingNetworkTransfer


class GameStateDiff(SupportsNetworkTransfer, SupportsDiff):
    def __init__(self, step: TimeStep):
        self.step = step
        self.player_state: dict[str, PlayerStateDiff] = {}

    def transfer(self, builder: SupportsBuildingNetworkTransfer):
        builder.add(
            "game_step",
            f"{self.step.begin} {self.step.end}"
        )
        for player in self.player_state.values():
            player.transfer(builder)

    def restore(self, transfer):
        step = transfer.get("game_step").split(" ")
        for player in self.player_state.values():
            player.restore(transfer)

    def apply(self, other: 'GameStateDiff'):
        self.step = TimeStep(begin=self.step.begin, end=other.step.end)
        for id, state in other.player_state.items():
            self.player_state[id].apply(state)

    def diff(self, other: 'GameStateDiff') -> 'GameStateDiff':
        if other.step.end < self.step.end:
            raise RuntimeError("invalid order of game states to diff")

        diff_state = GameStateDiff(TimeStep(self.step.end, other.step.end))
        for id, state in self.player_state.items():
            diff_state.player_state[id] = self.player_state[id].diff(other.player_state[id])
            list(self.player_state.keys()).sort()

        return diff_state

    @classmethod
    def empty(cls, player_ids=[]):
        game_state = cls(TimeStep(begin=0, end=0))
        for id in player_ids:
            game_state.player_state[id] = PlayerStateDiff.empty(id)
        return game_state

    def clone(self):
        cloned = GameStateDiff(self.step)
        for id, player_state in self.player_state.items():
            cloned.player_state[id] = player_state.clone()
        return cloned
