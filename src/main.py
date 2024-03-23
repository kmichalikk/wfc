import panda3d.core as p3d
import simplepbr

from direct.showbase.ShowBase import ShowBase
from direct.task.TaskManagerGlobal import taskMgr
from panda3d.core import CollisionTraverser, CollisionHandlerPusher, CollisionNode, CollisionTube

from src.player.player_controller import Player
from src.tiles.tile_node_path_factory import TileNodePathFactory
from src.tiles.tile_controller import create_new_tile
from src.tiles.tile_controller import collision_shapes
from src.wfc_starter import start_wfc


class Game(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)

        map_size = 10

        simplepbr.init()
        self.disableMouse()

        properties = p3d.WindowProperties()
        properties.set_size(1280, 800)
        self.win.request_properties(properties)

        point_light_node = self.render.attach_new_node(p3d.PointLight("light"))
        point_light_node.set_pos(0, -10, 10)
        self.render.set_light(point_light_node)

        self.cTrav = CollisionTraverser()
        self.pusher = CollisionHandlerPusher()
        self.pusher.setHorizontal(True)

        node_path_factory = TileNodePathFactory(self.loader)
        tiles, player_positions = start_wfc(map_size, 5)

        player_node_path = node_path_factory.get_player_model()
        player_node_path.set_pos(player_positions[0])
        player_node_path.reparent_to(self.render)

        self.player = Player(player_node_path)
        self.attach_input(self.player)
        self.player_movement_task = taskMgr.add(self.player.update_position, "update player position")

        collider = self.player.collider
        # collider.show()
        self.cTrav.addCollider(collider, self.pusher)
        self.pusher.addCollider(collider, self.player.model)
        self.pusher.setHorizontal(True)

        tile: p3d.NodePath
        for tile_data in tiles:
            tile = create_new_tile(self.loader, tile_data["node_path"], tile_data["pos"], tile_data["heading"])
            tile.reparent_to(self.render)
            self.create_exclusion_zone(tile, tile_data["node_path"])

        # self.camera.set_pos(self.player.model.getX(), self.player.model.getY()-3, 7)
        # self.camera.lookAt(self.player.model)
        # self.taskMgr.add(self.update_camera, "UpdateCamera")

        self.camera.set_pos(10, 10, 50)
        self.camera.look_at(10, 10, 0)

        self.create_borders(map_size)

    def update_camera(self, task):
        self.camera.setPos(self.player.model.getX(), self.player.model.getY()-3, 7)
        return task.cont

    @staticmethod
    def create_exclusion_zone(tile, name):
        zones = collision_shapes[name]
        if zones:
            exclusion_zone = CollisionNode(name)
            for zone in zones:
                exclusion_zone.add_solid(zone)

            exclusion_node_path = tile.attach_new_node(exclusion_zone)
            # exclusion_node_path.show()

    def create_borders(self, map_size):
        collision_tubes = [
            CollisionTube(-2, -2, 0, map_size * 2, -2, 0, 1),
            CollisionTube(-2, map_size * 2, 0, map_size * 2, map_size * 2, 0, 1),
            CollisionTube(-2, -2, 0, -2, map_size * 2, 0, 1),
            CollisionTube(map_size * 2, -2, 0, map_size * 2, map_size * 2, 0, 1)
        ]
        for tube in collision_tubes:
            wall_shape = tube
            wall_node = CollisionNode("wall")
            wall_node.addSolid(wall_shape)
            wall = self.render.attachNewNode(wall_node)
            wall.show()

    def attach_input(self, player: Player):
        self.accept("w", lambda: player.motion.update_input("+forward"))
        self.accept("w-up", lambda: player.motion.update_input("-forward"))
        self.accept("s", lambda: player.motion.update_input("+backward"))
        self.accept("s-up", lambda: player.motion.update_input("-backward"))
        self.accept("d", lambda: player.motion.update_input("+right"))
        self.accept("d-up", lambda: player.motion.update_input("-right"))
        self.accept("a", lambda: player.motion.update_input("+left"))
        self.accept("a-up", lambda: player.motion.update_input("-left"))


app = Game()
app.run()
