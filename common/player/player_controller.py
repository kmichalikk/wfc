from panda3d.core import NodePath, Vec3
from common.player.motion import Motion


class PlayerController:
    def __init__(self, model: NodePath, connection=None, id=""):
        self.model = model
        self.motion = Motion(model.get_pos())
        self.connection = connection
        self.id = id

    def update_position_task(self, task):
        self.motion.update()
        return self.sync_position_task(task)

    def sync_position_task(self, task):
        self.sync_position()
        return task.cont

    def sync_position(self):
        self.model.set_pos(self.motion.position)
        self.model.set_h(self.motion.angle)

    def update_input(self, input):
        self.motion.update_input(input)
        self.connection.update_input(input)

    def set_id(self, id):
        self.id = id

    def fill_motion(self, datagram_iterator):
        self.motion.fill(datagram_iterator)

    def dump_motion(self, datagram):
        self.motion.dump(datagram)
