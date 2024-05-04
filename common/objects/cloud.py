import panda3d.core as p3d
from direct.showbase.ShowBaseGlobal import globalClock
from direct.task.TaskManagerGlobal import taskMgr


class Cloud:
    def __init__(self, node_path: p3d.NodePath, max_scale: float):
        self.node_path = node_path
        self.max_scale = max_scale
        self.t = min(0.1, max_scale)
        self.scale = p3d.Vec3(self.t, self.t, self.t)
        self.node_path.set_scale(self.scale)
        self.decreasing = False
        self.started = False

    def inflate(self):
        if not self.started:
            self.started = True
            taskMgr.add(self.inflate_task, "inflate")

    def rescale(self, scale):
        self.scale.set_x(scale)
        self.scale.set_y(scale)
        self.scale.set_z(scale)
        self.node_path.set_scale(self.scale)

    def inflate_task(self, task):
        self.t += globalClock.get_dt() * 6
        new_scale_factor = (1 - (1 - self.t) ** 5) * self.max_scale
        self.rescale(new_scale_factor)

        if self.t < 1:
            return task.cont
        else:
            self.t = 0
            taskMgr.add(self.deflate_task, "deflate")

    def deflate_task(self, task):
        self.t += globalClock.get_dt() * 6
        new_scale_factor = self.max_scale - self.t * self.max_scale
        self.rescale(new_scale_factor)
        if self.t < 1:
            return task.cont
        else:
            self.node_path.remove_node()
