import panda3d.core as p3d

from common.objects.cloud import Cloud


class CloudFactory:
    def __init__(self, loader, render):
        self.loader = loader
        self.render = render

    def spawn_cloud(self, pos: p3d.Vec3, max_scale: float, color: p3d.LColor):
        node_path = self.loader.load_model("../common/assets/models/cloud.glb")
        node_path.set_color(color)
        node_path.set_pos(pos)
        node_path.reparent_to(self.render)
        return Cloud(node_path, max_scale)
