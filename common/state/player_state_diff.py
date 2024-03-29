from panda3d.core import Vec3

from common.state.motion_state_diff import MotionStateDiff
from common.typings import SupportsDiff, SupportsNetworkTransfer, Item, Step, SupportsBuildingNetworkTransfer


class PlayerStateDiff(SupportsNetworkTransfer, SupportsDiff):
    def __init__(self, step: Step):
        self.step = step
        self.motion_state: MotionStateDiff = MotionStateDiff(
            self.step,
            Vec3.zero(),
            Vec3.zero(),
            Vec3.zero()
        )
        self.slot: Item = "empty"
        self.id: str = ""

    def apply(self, other: 'PlayerStateDiff'):
        self.step = Step(begin=self.step.begin, end=other.step.end, index=other.step.index)
        self.motion_state.apply(other.motion_state)
        self.slot = other.slot

    def diff(self, other: 'PlayerStateDiff') -> 'PlayerStateDiff':
        if other.step.begin < self.step.end:
            raise RuntimeError("invalid order of game states to diff")

        diff_state = PlayerStateDiff(Step(self.step.end, other.step.end, other.step.index))
        diff_state.motion_state = other.motion_state.diff(self.motion_state)
        diff_state.slot = other.slot

        return diff_state

    def transfer(self, builder: SupportsBuildingNetworkTransfer):
        pass
