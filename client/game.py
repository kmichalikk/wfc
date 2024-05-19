from typing import Callable
from direct.showbase.ShowBase import ShowBase
from direct.showbase.ShowBaseGlobal import aspect2d
import panda3d.core as p3d
import simplepbr

from common.objects.bolt_factory import BoltFactory
from common.typings import Input


class Game(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)
        # proper textures & lighting
        simplepbr.init()

        aspect2d.set_transparency(True)

        self.disableMouse()

        properties = p3d.WindowProperties()
        properties.set_size(800, 600)
        self.win.request_properties(properties)

        point_light = p3d.PointLight("light1")
        point_light_node1 = self.render.attach_new_node(point_light)
        point_light_node1.set_pos(0, 0, 20)
        ambient = p3d.AmbientLight("light2")
        ambient.set_color((0.02, 0.02, 0.02, 1))
        point_light_node2 = self.render.attach_new_node(ambient)
        self.render.set_light(point_light_node1)
        self.render.set_light(point_light_node2)

    def set_input_handler(self, input_handler: Callable[[Input], None]):
        self.accept("w", lambda: input_handler(Input("+forward")))
        self.accept("w-up", lambda: input_handler(Input("-forward")))
        self.accept("s", lambda: input_handler(Input("+backward")))
        self.accept("s-up", lambda: input_handler(Input("-backward")))
        self.accept("d", lambda: input_handler(Input("+right")))
        self.accept("d-up", lambda: input_handler(Input("-right")))
        self.accept("a", lambda: input_handler(Input("+left")))
        self.accept("a-up", lambda: input_handler(Input("-left")))

    def set_bullet_handler(self, bullet_handler: Callable[[], None]):
        self.accept("space-up", bullet_handler)

    def get_loader(self):
        return self.loader

    def get_render(self):
        return self.render

    def set_camera_pos(self, x, y, z):
        self.camera.set_pos(x, y, z)

    def set_camera_look_at(self, model: p3d.NodePath):
        self.camera.look_at(model)
