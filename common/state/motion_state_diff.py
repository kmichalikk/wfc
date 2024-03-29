from panda3d.core import Vec3

from common.transfer.network_transfer_builder import NetworkTransferBuilder
from common.typings import SupportsDiff, SupportsNetworkTransfer, Step


class MotionStateDiff(SupportsNetworkTransfer, SupportsDiff):
    def __init__(self, step: Step, position, velocity, acceleration):
        self.step = step
        self.position: Vec3 = position
        self.velocity: Vec3 = velocity
        self.acceleration: Vec3 = acceleration
        self.angle: float = 0

    def apply(self, other: 'MotionStateDiff'):
        self.step = Step(begin=self.step.begin, end=other.step.end, index=other.step.index)
        self.position += other.position
        self.velocity += other.velocity
        self.acceleration += other.acceleration
        self.angle += other.angle

    def diff(self, other: 'MotionStateDiff') -> 'MotionStateDiff':
        if other.step.begin < self.step.end:
            raise RuntimeError("invalid order of game states to diff")

        diff_state = MotionStateDiff(
            Step(self.step.end, other.step.end, other.step.index),
            other.position - self.position,
            other.velocity - self.velocity,
            other.acceleration - self.acceleration
        )
        diff_state.angle = other.angle - self.angle

        return diff_state

    def transfer(self, builder: NetworkTransferBuilder):
        pass
