import simplepbr
from direct.showbase.ShowBase import ShowBase
import panda3d.core as p3d

from src.tiles.TileNodePathFactory import TileNodePathFactory


class Game(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)

        # initialize Physics Based Rendering
        simplepbr.init()
        # disable default mouse movement in order to set the camera to fixed position
        self.disableMouse()

        # set window size
        properties = p3d.WindowProperties()
        properties.set_size(800, 600)
        self.win.request_properties(properties)

        # add lighting
        point_light_node = self.render.attach_new_node(p3d.PointLight("light"))
        point_light_node.set_pos(-10, -10, 10)
        self.render.set_light(point_light_node)

        # render tiles - POC
        node_path_factory = TileNodePathFactory(self.loader)
        tiles = [
            {"node_path": node_path_factory.get_tile_node_path("wall_straight_1"), "pos": (-1, 1, 0), "heading": 0},
            {"node_path": node_path_factory.get_tile_node_path("wall_convex_1"), "pos": (1, 1, 0), "heading": -90},
            {"node_path": node_path_factory.get_tile_node_path("plants_1"), "pos": (-1, -1, 0), "heading": 0},
            {"node_path": node_path_factory.get_tile_node_path("wall_straight_2"), "pos": (1, -1, 0), "heading": -90},
        ]

        tile_node_path: p3d.NodePath
        for tile in tiles:
            tile_node_path = tile["node_path"]
            tile_node_path.set_pos(*tile["pos"])
            tile_node_path.set_h(tile["heading"])
            tile_node_path.reparent_to(self.render)

        self.camera.set_pos(0, -10, 10)
        self.camera.look_at(0, 0, 0)


app = Game()
app.run()
