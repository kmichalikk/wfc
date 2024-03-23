import os
import pickle

import panda3d.core as p3d
from direct.distributed.PyDatagram import PyDatagram
from direct.distributed.PyDatagramIterator import PyDatagramIterator
from direct.showbase.ShowBase import ShowBase
from direct.task.TaskManagerGlobal import taskMgr

from common.player.player_controller import Player
from common.tiles.tile_node_path_factory import TileNodePathFactory
from common.typings import Messages
from server.wfc_starter import start_wfc


class Server(ShowBase):
    def __init__(self):
        super().__init__(windowType="none")
        self.connection_manager = p3d.ConnectionManager()
        self.connection_listener = p3d.QueuedConnectionListener(self.connection_manager, 0)
        self.connection_reader = p3d.QueuedConnectionReader(self.connection_manager, 0)
        self.connection_writer = p3d.ConnectionWriter(self.connection_manager, 0)
        self.active_connections = {}
        self.players = {}
        self.global_state_index = 0
        self.node_path_factory = TileNodePathFactory(self.loader)
        print("[INFO] Starting WFC map generation")
        self.tiles, self.player_positions = start_wfc(10, 1)
        print("[INFO] Map generated")
        taskMgr.add(self.broadcast_global_state, "broadcast global state")

    def listen(self, port):
        tcp_socket = self.connection_manager.open_TCP_server_rendezvous(port, 1000)
        self.connection_listener.add_connection(tcp_socket)
        taskMgr.add(self.poll_listener, "poll the connection listener", -39)
        taskMgr.add(self.poll_reader, "poll the connection reader", -40)
        print(f"[INFO] Server started on port {port}")

    def poll_listener(self, task):
        if self.connection_listener.new_connection_available():
            rendezvous = p3d.PointerToConnection()
            net_address = p3d.NetAddress()
            new_connection = p3d.PointerToConnection()
            if self.connection_listener.get_new_connection(rendezvous, net_address, new_connection):
                new_connection = new_connection.p()
                new_connection.set_no_delay(True)
                print(f"[INFO] New connection from {new_connection.get_address()}")
                self.connection_reader.add_connection(new_connection)
                player_id = str(hash(new_connection.get_address()))
                player = Player(self.node_path_factory.get_player_model(), id=player_id)
                self.players[player_id] = player
                self.active_connections[player_id] = new_connection
                taskMgr.add(player.update_position, "update player position")

        return task.cont

    def poll_reader(self, task):
        if self.connection_reader.data_available():
            datagram = p3d.NetDatagram()
            if self.connection_reader.get_data(datagram):
                datagram_iterator = PyDatagramIterator(datagram)
                message = datagram_iterator.get_uint8()
                self.handle_message(message, datagram_iterator, datagram.get_connection())
        return task.cont

    def broadcast_global_state(self, task):
        datagram = PyDatagram()
        datagram.add_uint32(self.global_state_index)
        self.global_state_index += 1
        datagram.add_uint8(len(self.players))
        for id, player in self.players.items():
            datagram.add_string(id)
            motion_vectors = (player.motion.acceleration, player.motion.velocity, player.motion.position)
            for v in motion_vectors:
                datagram.add_float32(v.get_x())
                datagram.add_float32(v.get_y())
        for player in self.players.values():
            self.connection_writer.send(datagram, self.active_connections[player.id])
            print(self.global_state_index)
        return task.cont

    def handle_message(self, message, datagram_iterator, origin_connection):
        print(f"[INFO] Received message: {Messages(message).name}")
        if message == Messages.FIND_ROOM:
            datagram = PyDatagram()
            datagram.add_uint8(Messages.FIND_ROOM_OK)
            # todo: send room data
            self.connection_writer.send(datagram, origin_connection)
        elif message == Messages.ACCEPT_ROOM:
            datagram = PyDatagram()
            datagram.add_uint8(Messages.ACCEPT_ROOM_OK)
            datagram.add_blob(pickle.dumps(self.tiles))
            datagram.add_string(str(hash(origin_connection.get_address())))
            self.connection_writer.send(datagram, origin_connection)
        elif message == Messages.UPDATE_INPUT:
            input = datagram_iterator.get_string()
            self.players[str(hash(origin_connection.get_address()))].motion.update_input(input)
        elif message == Messages.GLOBAL_STATE:
            datagram = PyDatagram()
            datagram.add_uint8(Messages.ACCEPT_ROOM_OK)
            datagram.add_blob(pickle.dumps(self.tiles))
            self.connection_writer.send(datagram, origin_connection)


if __name__ == "__main__":
    server = Server()
    server.set_sleep(0.016)
    server.listen(os.environ.get("PORT", 7654))
    server.run()
