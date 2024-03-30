import sys
import time
import panda3d.core as p3d
import simplepbr

from direct.showbase.ShowBase import ShowBase
from direct.task.TaskManagerGlobal import taskMgr
from panda3d.core import Vec3

from common.collision.border import Border
from common.collision.collision_object import CollisionObject
from common.config.game_config import GameConfig
from common.player.player_controller import PlayerController
from common.state.game_state_diff import GameStateDiff
from common.state.player_state_diff import PlayerStateDiff
from common.tiles.tile_controller import create_new_tile, collision_shapes
from common.tiles.tile_node_path_factory import TileNodePathFactory
from common.connection.udp_connection_thread import UDPConnectionThread
from common.transfer.network_transfer_builder import NetworkTransferBuilder
from common.typings import Messages, Address, TimeStep
from server.wfc.wfc_starter import start_wfc

sys.path.append("../common")


class Server(ShowBase):
    def __init__(self, address, port, view=False):
        if view:
            super().__init__()
        else:
            super().__init__(windowType="none")
        self.view = view
        self.port = port
        self.udp_connection = UDPConnectionThread(address, port)
        self.node_path_factory = TileNodePathFactory(self.loader)
        self.network_transfer_builder = NetworkTransferBuilder()
        self.active_players: dict[Address, PlayerController] = {}
        self.next_id = 0
        self.map_size = 10
        print("[INFO] Starting WFC map generation")
        self.tiles, self.player_positions = start_wfc(self.map_size, 1)
        self.__setup_collisions()
        print("[INFO] Map generated")
        if self.view:
            self.__setup_view()

    def listen(self):
        self.udp_connection.start()
        taskMgr.add(self.handle_clients, "handle client messages")
        taskMgr.add(self.broadcast_global_state, "broadcast global state")
        print(f"[INFO] Listening on port {self.port}")

    def handle_clients(self, task):
        for transfer in self.udp_connection.get_queued_transfers():
            type = transfer.get("type")
            if type == Messages.HELLO:
                print("[INFO] New client")
            elif type == Messages.FIND_ROOM:
                print("[INFO] Room requested")
                new_player_controller = self.__add_new_player(transfer.get_source(), str(self.next_id))
                self.network_transfer_builder.add("id", str(self.next_id))
                self.next_id += 1
                self.network_transfer_builder.set_destination(transfer.get_source())
                self.network_transfer_builder.add("type", Messages.FIND_ROOM_OK)
                game_config = GameConfig(
                    self.tiles,
                    new_player_controller.get_id(),
                    [player.get_state() for player in self.active_players.values()]
                )
                game_config.transfer(self.network_transfer_builder)
                self.udp_connection.enqueue_transfer(self.network_transfer_builder.encode())
                self.broadcast_new_player(
                    new_player_controller.get_id(),
                    new_player_controller.get_state()
                )
            elif type == Messages.UPDATE_INPUT:
                print("[INFO] Update input")
                if transfer.get_source() in self.active_players:
                    self.active_players[transfer.get_source()].update_input(transfer.get("input"))
        return task.cont

    def broadcast_global_state(self, task):
        game_state = GameStateDiff(TimeStep(begin=0, end=time.time()))
        player: PlayerController
        game_state.player_state \
            = {player.get_id(): player.get_state() for player in self.active_players.values()}
        self.network_transfer_builder.add("type", Messages.GLOBAL_STATE)
        game_state.transfer(self.network_transfer_builder)
        address: Address
        for address in self.active_players.keys():
            self.network_transfer_builder.set_destination(address)
            self.udp_connection.enqueue_transfer(
                self.network_transfer_builder.encode(reset=False)
            )
        self.network_transfer_builder.cleanup()
        return task.cont

    def broadcast_player_disconnected(self, task):
        # todo: client is active as long as it sends KEEP_ALIVE from time to time
        #       if it haven't send anything for a minute, then remove it and notify others
        pass

    def broadcast_new_player(self, player_id, state):
        self.network_transfer_builder.add("type", Messages.NEW_PLAYER)
        self.network_transfer_builder.add("id", player_id)
        state.transfer(self.network_transfer_builder)
        print("[INFO] Notifying players about new player")
        for address, player in self.active_players.items():
            if player.get_id() == player_id:
                continue
            self.network_transfer_builder.set_destination(address)
            self.udp_connection.enqueue_transfer(
                self.network_transfer_builder.encode(reset=False)
            )
        self.network_transfer_builder.cleanup()

    def __add_new_player(self, address: Address, id: str) -> PlayerController:
        new_player_state = PlayerStateDiff(TimeStep(begin=0, end=time.time()), id)
        new_player_state.set_position(self.player_positions[0])
        model = self.node_path_factory.get_player_model()
        model.reparent_to(self.render)
        new_player_controller = PlayerController(model, new_player_state)
        self.active_players[address] = new_player_controller

        player_collider = new_player_controller.colliders[0]
        self.cTrav.addCollider(player_collider, self.pusher)
        self.pusher.addCollider(player_collider, player_collider)
        if self.view:
            player_collider.show()

        taskMgr.add(new_player_controller.update_position, "update player position")

        return new_player_controller

    def __setup_collisions(self):
        self.cTrav = p3d.CollisionTraverser()
        self.pusher = p3d.CollisionHandlerPusher()
        self.pusher.setHorizontal(True)

        self.border = Border(self.render, self.map_size)
        self.tile_colliders = []

        tile: p3d.NodePath
        for tile_data in self.tiles:
            tile = create_new_tile(self.loader, tile_data["node_path"], tile_data["pos"], tile_data["heading"])
            tile.reparent_to(self.render)
            self.tile_colliders.append(CollisionObject(tile, tile_data["node_path"],
                                                       collision_shapes[tile_data["node_path"]]))

    def __setup_view(self):
        simplepbr.init()
        self.disableMouse()

        properties = p3d.WindowProperties()
        properties.set_size(1280, 800)
        self.win.request_properties(properties)

        point_light_node = self.render.attach_new_node(p3d.PointLight("light"))
        point_light_node.set_pos(0, -10, 10)
        self.render.set_light(point_light_node)
        self.camera.set_pos(Vec3(self.map_size, self.map_size, 5 * self.map_size))
        self.camera.look_at(Vec3(self.map_size, self.map_size, 0))
        for c in self.tile_colliders:
            c.show()


if __name__ == "__main__":
    server = Server('127.0.0.1', 7654)
    server.set_sleep(0.016)
    server.listen()
    print(f"[INFO] Starting game loop")
    server.run()
