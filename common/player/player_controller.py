import time

from panda3d.core import NodePath, CollisionSphere, Vec3
from common.collision.collision_object import CollisionObject
from common.state.player_state_diff import PlayerStateDiff
from common.typings import Input, TimeStep


class PlayerController(CollisionObject):
    def __init__(self, model: NodePath, player_state: PlayerStateDiff, ghost=False):
        if ghost:
            # todo: refactor - ghost as separate class (without collision object, identical otherwise)
            super().__init__(parent=model.parent, name="player", shapes=[CollisionSphere(0, 0, 5, 0.25)])
        else:
            super().__init__(parent=model.parent, name="player", shapes=[CollisionSphere(0, 0, 0.5, 0.25)])

        self.model = model
        if ghost:
            self.model.hide()
        self.state = player_state

    def get_id(self) -> str:
        return self.state.id

    def get_state(self) -> PlayerStateDiff:
        return self.state

    def replace_state(self, state: PlayerStateDiff):
        state.motion_state.active_inputs = self.state.motion_state.active_inputs
        self.state = state
        self.colliders[0].set_pos(self.state.get_position())

    def update_input(self, input: Input):
        self.state.motion_state.update_input(input)

    def update_position(self):
        self.state.set_position(self.colliders[0].get_pos())
        self.state.update_motion()
        self.sync_position()
        self.update_time_step()

    def sync_position(self):
        self.colliders[0].set_pos(self.state.get_position())
        self.model.set_pos(self.state.get_position())
        self.model.set_h(self.state.get_model_angle())
        self.update_time_step()

    def task_update_position(self, task):
        self.update_position()
        return task.cont

    def update_time_step(self):
        self.state.step = TimeStep(self.state.step.begin, time.time())
        self.state.motion_state.step = TimeStep(self.state.motion_state.step.begin, time.time())
