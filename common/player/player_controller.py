from panda3d.core import NodePath, Vec3
from common.player.motion import Motion


class Player:
    def __init__(self, model: NodePath, connection=None, id=None):
        self.model = model
        self.motion = Motion(model.get_pos())
        self.connection = connection
        self.id = id

    def update_position(self, task):
        self.motion.update()
        return self.sync_position(task)

    def sync_position(self, task):
        self.model.set_pos(self.motion.position)
        if self.motion.velocity.length() > 0.01:
            self.model.set_h(-self.motion.velocity.normalized().signed_angle_deg(Vec3(0, 1, 0), Vec3(0, 0, 1)))
        return task.cont

    def update_input(self, input):
        self.motion.update_input(input)
        self.connection.update_input(input)

    def set_motion(self, motion):
        self.motion = motion

    def set_id(self, id):
        self.id = id

    def __getstate__(self):
        state = self.__dict__.copy()
        del state["model"]
        del state["connection"]
        return state
