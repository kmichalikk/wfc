import os
from direct.showbase.ShowBase import ShowBase
from direct.task.TaskManagerGlobal import taskMgr

from client.connect.connect import Connection
from common.player.player_controller import PlayerController
from common.tiles.tile_node_path_factory import TileNodePathFactory
import simplepbr
import panda3d.core as p3d


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
        self.node_path_factory = TileNodePathFactory(self.loader)

        self.all_players = {}

        connection = Connection()
        connection.initialize("127.0.0.1", os.environ.get("PORT", 7654))

        def render(player_id):
            tiles = connection.tiles
            for tile in tiles:
                tile["node_path"] = self.node_path_factory.get_tile_node_path(tile["node_path"])

            tile_node_path: p3d.NodePath
            for tile in tiles:
                tile_node_path = tile["node_path"]
                tile_node_path.set_pos(*tile["pos"])
                tile_node_path.set_h(tile["heading"])
                tile_node_path.reparent_to(self.render)

            self.camera.set_pos(10, -20, 20)
            self.camera.look_at(10, 10, 0)

            player_node_path = self.node_path_factory.get_player_model()
            player_node_path.set_pos(p3d.Vec3(5, 5, 0))
            player_node_path.reparent_to(self.render)
            self.player = PlayerController(player_node_path, connection, player_id)
            self.all_players[player_id] = self.player
            self.attach_input(self.player)
            self.player_movement_task = taskMgr.add(self.player.sync_position_task, "update player position")
            connection.set_sync_task(self.sync)

        connection.find_room(render)

    def sync(self, datagram_iterator):
        num_players = datagram_iterator.get_uint8()
        for _ in range(num_players):
            id = datagram_iterator.get_string()
            if id not in self.all_players:
                player_node = self.node_path_factory.get_player_model()
                player_node.reparent_to(self.render)
                self.all_players[id] = PlayerController(player_node, id=id)
            self.all_players[id].fill_motion(datagram_iterator)
            self.all_players[id].sync_position()

    def attach_input(self, player: PlayerController):
        self.accept("w", lambda: player.update_input("+forward"))
        self.accept("w-up", lambda: player.update_input("-forward"))
        self.accept("s", lambda: player.update_input("+backward"))
        self.accept("s-up", lambda: player.update_input("-backward"))
        self.accept("d", lambda: player.update_input("+right"))
        self.accept("d-up", lambda: player.update_input("-right"))
        self.accept("a", lambda: player.update_input("+left"))
        self.accept("a-up", lambda: player.update_input("-left"))


app = Game()
app.run()
