import time
from typing import Union

import panda3d.core as p3d
import random

from common.collision.collision_object import CollisionObject
from common.objects.cloud_factory import CloudFactory
from common.state.player_state_diff import PlayerStateDiff
from common.typings import Input, TimeStep


class PlayerController(CollisionObject):
    COLLISION_RADIUS = 0.3

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
        self.cloud_factory: Union[CloudFactory, None] = None
        self.emit_cloud = True
        self.cloud_color = p3d.LColor(0.73, 0.76, 0.67, 1)
        if ghost:  # comment out to see the server ghost
            self.model.hide()
        self.state = player_state

    def get_id(self) -> str:
        return self.state.id

    def get_state(self) -> PlayerStateDiff:
        return self.state

    def set_cloud_factory(self, factory: CloudFactory):
        self.cloud_factory = factory

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
        self.state.update_angle()
        self.colliders[0].set_pos(self.state.get_position())
        self.model.set_pos(self.state.get_position())
        self.model.set_h(self.state.get_model_angle())
        self.update_time_step()

    def task_emit_cloud(self, task):
        """
        emits cloud if player is moving; should be used with do_method_later()
        """
        if self.emit_cloud and self.cloud_factory is not None:
            velocity = self.state.motion_state.velocity.length()
            scale = velocity / self.state.motion_state.target_velocity * (1 + random.random())
            if scale > 0.1:
                position_offset = p3d.Vec3(
                    -0.1 * self.state.motion_state.direction.get_x() + random.random() / 4 - 0.125,
                    -0.1 * self.state.motion_state.direction.get_y() + random.random() / 4 - 0.125,
                    0.15
                )
                position = self.get_state().get_position() + position_offset
                self.cloud_factory \
                    .spawn_cloud(position, scale, self.cloud_color) \
                    .inflate()
        return task.again

    def task_update_position(self, task):
        self.update_position()
        self.sync_position()
        return task.cont

    def update_time_step(self):
        self.state.step = TimeStep(self.state.step.begin, time.time())
        self.state.motion_state.step = TimeStep(self.state.motion_state.step.begin, time.time())
