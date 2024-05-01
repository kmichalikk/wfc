import time
import panda3d.core as p3d

from common.collision.collision_object import CollisionObject
from common.state.player_state_diff import PlayerStateDiff
from common.typings import Input, TimeStep


class PlayerController(CollisionObject):
    COLLISION_RADIUS = 0.25

    def __init__(self, model: p3d.NodePath, player_state: PlayerStateDiff, ghost=False):
        if ghost:
            # todo: refactor - ghost as separate class (without collision object, identical otherwise)
            super().__init__(parent=model.parent, name="player" + player_state.id,
                             shapes=[p3d.CollisionSphere(0, 0, 5, self.COLLISION_RADIUS)])
        else:
            super().__init__(parent=model.parent, name="player" + player_state.id,
                             shapes=[p3d.CollisionSphere(0, 0, 0.5, self.COLLISION_RADIUS)])

        self.model = model
        self.colliders[0].set_tag('id', player_state.id)
        if ghost:  # comment out to see the server ghost
            self.model.hide()
        self.state = player_state

    def get_id(self) -> str:
        return self.state.id

    def get_state(self) -> PlayerStateDiff:
        return self.state

    def has_flag(self):
        if self.state.slot == "flag":
            return True
        return False

    def replace_state(self, state: PlayerStateDiff):
        state.motion_state.active_inputs = self.state.motion_state.active_inputs
        self.state = state
        self.colliders[0].set_pos(self.state.get_position())

    def update_input(self, input: Input):
        self.state.motion_state.update_input(input)

    def update_position(self):
        self.state.set_position(self.colliders[0].get_pos())
        self.state.update_motion()

    def sync_position(self):
        self.colliders[0].set_pos(self.state.get_position())
        self.model.set_pos(self.state.get_position())
        self.model.set_h(self.state.get_model_angle())
        self.update_time_step()

    def task_update_position(self, task):
        self.update_position()
        self.sync_position()
        return task.cont

    def update_time_step(self):
        self.state.step = TimeStep(self.state.step.begin, time.time())
        self.state.motion_state.step = TimeStep(self.state.motion_state.step.begin, time.time())

    def into_safe_space(self, entry):
        if entry.getFromNodePath().getName()[-1] == entry.getIntoNodePath().getName()[-1] and self.has_flag:
            print("Player " + self.get_id() + " has won the game!")
