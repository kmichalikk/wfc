from panda3d.core import NodePath, Vec3, CollisionSphere
from common.collision.collision_object import CollisionObject
from common.state.player_state_diff import PlayerStateDiff
from common.typings import Input


class PlayerController(CollisionObject):
    def __init__(self, model: NodePath, player_state: PlayerStateDiff):
        super().__init__(parent=model.parent, name="player", shapes=[CollisionSphere(0, 0, 0.5, 0.25)])

        self.model = model
        self.state = player_state

    def update_input(self, input: Input):
        self.state.motion_state.update_input(input)

    def update_position(self, task):
        self.state.set_position(self.colliders[0].get_pos())
        self.state.update_motion()
        self.colliders[0].set_pos(self.state.get_position())
        self.model.set_pos(self.colliders[0].get_pos())
        self.model.set_h(self.state.get_model_angle())
        return task.cont
