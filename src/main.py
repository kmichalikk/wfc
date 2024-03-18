import simplepbr
from direct.showbase.ShowBase import ShowBase
import panda3d.core as p3d
from src.wfc_starter import start_wfc
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
        properties.set_size(1280, 800)
        self.win.request_properties(properties)

        # add lighting
        point_light_node = self.render.attach_new_node(p3d.PointLight("light"))
        point_light_node.set_pos(0, -10, 10)
        self.render.set_light(point_light_node)

        node_path_factory = TileNodePathFactory(self.loader)
        tiles = start_wfc(10, 1)
        for tile in tiles:
            tile["node_path"] = node_path_factory.get_tile_node_path(tile["node_path"])

        tile_node_path: p3d.NodePath
        for tile in tiles:
            tile_node_path = tile["node_path"]
            tile_node_path.set_pos(*tile["pos"])
            tile_node_path.set_h(tile["heading"])
            tile_node_path.reparent_to(self.render)

        self.camera.set_pos(10, -20, 20)
        self.camera.look_at(10, 10, 0)


app = Game()
app.run()
