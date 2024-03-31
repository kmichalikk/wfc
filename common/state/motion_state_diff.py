from direct.showbase.ShowBaseGlobal import globalClock
from panda3d.core import Vec3

from common.typings import SupportsDiff, SupportsNetworkTransfer, TimeStep, SupportsBuildingNetworkTransfer, Input


class MotionStateDiff(SupportsNetworkTransfer, SupportsDiff):
    def __init__(self, step: TimeStep, position, velocity, acceleration, player_id):
        self.player_id = player_id
        self.step = step
        self.position: Vec3 = position
        self.velocity: Vec3 = velocity
        self.acceleration: Vec3 = acceleration
        self.angle: float = 0

        self.active_inputs: Vec3 = Vec3(0, 0, 0)
        self.acceleration_rate = 0.5
        self.damping = 0.01

    def apply(self, other: 'MotionStateDiff'):
        self.step = TimeStep(begin=self.step.begin, end=other.step.end)
        self.position += other.position
        self.velocity += other.velocity
        self.acceleration += other.acceleration
        self.angle += other.angle

    def diff(self, other: 'MotionStateDiff') -> 'MotionStateDiff':
        if other.step.end < self.step.end:
            # when it prints too often, it's likely there are bugs in code
            print("invalid order of game states to diff")

        diff_state = MotionStateDiff(
            TimeStep(self.step.end, other.step.end),
            other.position - self.position,
            other.velocity - self.velocity,
            other.acceleration - self.acceleration,
            self.player_id
        )
        diff_state.angle = other.angle - self.angle

        return diff_state

    def lerp(self, t: float, other: 'MotionStateDiff') -> 'MotionStateDiff':
        lerp_state = MotionStateDiff(
            self.step,
            (other.position - self.position) * t,
            0,
            0,
            self.player_id
        )
        lerp_state.angle = (other.angle - self.angle) * t

        return lerp_state

    def transfer(self, builder: SupportsBuildingNetworkTransfer):
        builder.add(
            f"m{self.player_id}step",
            f"{self.step.begin} {self.step.end}"
        )
        builder.add(f"m{self.player_id}px", str(self.position.get_x()))
        builder.add(f"m{self.player_id}py", str(self.position.get_y()))
        builder.add(f"m{self.player_id}vx", str(self.velocity.get_x()))
        builder.add(f"m{self.player_id}vy", str(self.velocity.get_y()))
        builder.add(f"m{self.player_id}ax", str(self.acceleration.get_x()))
        builder.add(f"m{self.player_id}ay", str(self.acceleration.get_y()))
        builder.add(f"m{self.player_id}ang", str(self.angle))

    def restore(self, transfer):
        step = transfer.get(f"p{self.player_id}step").split(" ")
        self.step = TimeStep(float(step[0]), float(step[1]))
        self.position.set_x(float(transfer.get(f"m{self.player_id}px")))
        self.position.set_y(float(transfer.get(f"m{self.player_id}py")))
        self.velocity.set_x(float(transfer.get(f"m{self.player_id}vx")))
        self.velocity.set_y(float(transfer.get(f"m{self.player_id}vy")))
        self.acceleration.set_x(float(transfer.get(f"m{self.player_id}ax")))
        self.acceleration.set_y(float(transfer.get(f"m{self.player_id}ay")))
        self.angle = float(transfer.get(f"m{self.player_id}ang"))

    def update(self):
        """ updates motion, makes sense only for full diffs (step.begin == 0) """
        dt = globalClock.get_dt()
        self.velocity.set_x((self.velocity.get_x() + self.acceleration.get_x() * dt) * self.damping ** dt)
        self.velocity.set_y((self.velocity.get_y() + self.acceleration.get_y() * dt) * self.damping ** dt)
        self.position.set_x(self.position.get_x() + self.velocity.get_x() * self.damping ** dt)
        self.position.set_y(self.position.get_y() + self.velocity.get_y() * self.damping ** dt)
        if self.velocity.length() > 0.01:
            self.angle = -self.velocity.normalized().signed_angle_deg(Vec3(0, 1, 0), Vec3(0, 0, 1))

    def cut_end(self, new_end: float):
        """
        simple approximation when we need shorter part of the motion_diff
        useful for short diffs (not beginning from 0)
        """
        if new_end > self.step.end:
            return self

        # calculate new/old ratio t between [0, 1] (check for zero division)
        span = self.step.end - self.step.begin
        t = (new_end - self.step.begin) / span if span > 0.001 else 0

        return MotionStateDiff(
            TimeStep(
                begin=self.step.begin,
                end=new_end
            ),
            self.position * t,
            self.velocity * (1 - (1-t)**2),
            self.acceleration,
            self.player_id
        )

    def update_input(self, input: Input):
        match input:
            case "+forward": self.active_inputs.add_y(1)
            case "-forward": self.active_inputs.add_y(-1)
            case "+backward": self.active_inputs.add_y(-1)
            case "-backward": self.active_inputs.add_y(1)
            case "+right": self.active_inputs.add_x(1)
            case "-right": self.active_inputs.add_x(-1)
            case "+left": self.active_inputs.add_x(-1)
            case "-left": self.active_inputs.add_x(1)
        normalized_inputs = self.active_inputs.normalized()
        self.acceleration.set_x(normalized_inputs.get_x() * self.acceleration_rate)
        self.acceleration.set_y(normalized_inputs.get_y() * self.acceleration_rate)

    @classmethod
    def empty(cls, player_id: str):
        return cls(
            TimeStep(begin=0, end=0),
            Vec3(0, 0, 0),
            Vec3(0, 0, 0),
            Vec3(0, 0, 0),
            player_id
        )

    def clone(self):
        cloned = MotionStateDiff(
            self.step,
            Vec3(self.position),
            Vec3(self.velocity),
            Vec3(self.acceleration),
            self.player_id
        )
        cloned.angle = self.angle
        return cloned
