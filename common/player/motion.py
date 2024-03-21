from direct.showbase.ShowBaseGlobal import globalClock
from panda3d.core import Vec3
from common.typings import Input


class Motion:
    def __init__(self, position: Vec3, velocity: Vec3 = None, acceleration: Vec3 = None):
        self.position: Vec3 = position
        self.velocity: Vec3 = velocity if velocity is not None else Vec3(0, 0, 0)
        self.acceleration: Vec3 = acceleration if acceleration is not None else Vec3(0, 0, 0)
        self.active_inputs: Vec3 = Vec3(0, 0, 0)
        self.acceleration_rate = 0.01
        self.damping = 0.01

    def update(self):
        dt = globalClock.get_dt()
        self.velocity.set_x((self.velocity.get_x() + self.acceleration.get_x()) * self.damping ** dt)
        self.velocity.set_y((self.velocity.get_y() + self.acceleration.get_y()) * self.damping ** dt)
        self.position.set_x(self.position.get_x() + self.velocity.get_x() * self.damping ** dt)
        self.position.set_y(self.position.get_y() + self.velocity.get_y() * self.damping ** dt)

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
