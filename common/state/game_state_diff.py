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
        self.step = TimeStep(float(step[0]), float(step[1]))
        for player in self.player_state.values():
            player.restore(transfer)

    def apply(self, other: 'GameStateDiff'):
        self.step = TimeStep(begin=self.step.begin, end=other.step.end)
        for id, state in other.player_state:
            self.player_state[id].apply(state)

    def diff(self, other: 'GameStateDiff') -> 'GameStateDiff':
        if other.step.begin < self.step.end:
            raise RuntimeError("invalid order of game states to diff")

        diff_state = GameStateDiff(TimeStep(self.step.end, other.step.end))
        for id, state in self.player_state:
            diff_state.player_state[id] = other.player_state[id].diff(self.player_state[id])
            list(self.player_state.keys()).sort()

        return diff_state

    @classmethod
    def empty(cls):
        return cls(TimeStep(begin=0, end=0))