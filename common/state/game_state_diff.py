from common.state.player_state_diff import PlayerStateDiff
from common.typings import SupportsDiff, SupportsNetworkTransfer, Step, SupportsBuildingNetworkTransfer


class GameStateDiff(SupportsNetworkTransfer, SupportsDiff):
    def __init__(self, step: Step):
        self.step = step
        self.player_state: dict[str, PlayerStateDiff] = {}

    def transfer(self, builder: SupportsBuildingNetworkTransfer):
        pass

    def apply(self, other: 'GameStateDiff'):
        self.step = Step(begin=self.step.begin, end=other.step.end, index=other.step.index)
        for id, state in other.player_state:
            self.player_state[id].apply(state)

    def diff(self, other: 'GameStateDiff') -> 'GameStateDiff':
        if other.step.begin < self.step.end:
            raise RuntimeError("invalid order of game states to diff")

        diff_state = GameStateDiff(Step(self.step.end, other.step.end, other.step.index))
        for id, state in self.player_state:
            diff_state.player_state[id] = other.player_state[id].diff(self.player_state[id])
            list(self.player_state.keys()).sort()

        return diff_state
