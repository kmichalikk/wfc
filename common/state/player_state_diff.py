from panda3d.core import Vec3

from common.state.motion_state_diff import MotionStateDiff
from common.typings import SupportsDiff, SupportsNetworkTransfer, Item, TimeStep, SupportsBuildingNetworkTransfer


class PlayerStateDiff(SupportsNetworkTransfer, SupportsDiff):
    def __init__(self, step: TimeStep, id: str, username: str):
        self.step = step
        self.motion_state: MotionStateDiff = MotionStateDiff.empty(id)
        self.slot: Item = "empty"
        self.id: str = id
        self.username: str = username
        self.energy = 10

    def apply(self, other: 'PlayerStateDiff'):
        self.step = TimeStep(begin=self.step.begin, end=other.step.end)
        self.motion_state.apply(other.motion_state)
        self.slot = other.slot
        self.username = other.username
        self.energy = other.energy

    def diff(self, other: 'PlayerStateDiff') -> 'PlayerStateDiff':
        if other.step.end < self.step.end:
            # when it prints too often, it's likely there are bugs in code
            print("invalid order of game states to diff")

        diff_state = PlayerStateDiff(TimeStep(self.step.end, other.step.end), self.id, other.username)
        diff_state.motion_state = self.motion_state.diff(other.motion_state)
        diff_state.slot = other.slot
        diff_state.energy = other.energy

        return diff_state

    def transfer(self, builder: SupportsBuildingNetworkTransfer):
        builder.add(
            f"p{self.id}step",
            f"{self.step.begin} {self.step.end}"
        )
        builder.add(f"p{self.id}slot", self.slot)
        builder.add(f"p{self.id}username", self.username)
        builder.add(f"p{self.id}energy", self.energy)

        self.motion_state.transfer(builder)

    def restore(self, transfer):
        step = transfer.get(f"p{self.id}step").split(" ")
        self.step = TimeStep(float(step[0]), float(step[1]))
        self.slot = transfer.get(f"p{self.id}slot")
        self.username = transfer.get(f"p{self.id}username")
        self.energy = transfer.get(f"p{self.id}energy")
        self.motion_state.restore(transfer)

    def get_position(self) -> Vec3:
        return self.motion_state.position

    def set_position(self, position: Vec3):
        self.motion_state.position = position

    def get_direction(self) -> Vec3:
        return self.motion_state.direction

    def get_model_angle(self) -> float:
        return self.motion_state.angle

    def pickup_flag(self):
        self.slot: Item = "flag"

    def drop_flag(self):
        self.slot: Item = "empty"

    def update_motion(self):
        """ works only for full diffs (step.begin == 0) """
        self.motion_state.update()

    def update_angle(self):
        self.motion_state.update_angle()

    @classmethod
    def empty(cls, player_id: str):
        return cls(TimeStep(begin=0, end=0), player_id,"")

    def clone(self):
        cloned = PlayerStateDiff(self.step, self.id, self.username)
        cloned.slot = self.slot
        cloned.energy = self.energy
        cloned.motion_state = self.motion_state.clone()
        return cloned
