import os
import pickle

import panda3d.core as p3d
from direct.distributed.PyDatagram import PyDatagram
from direct.distributed.PyDatagramIterator import PyDatagramIterator
from direct.showbase.ShowBase import ShowBase
from direct.task.TaskManagerGlobal import taskMgr
from common.tiles.tile_node_path_factory import TileNodePathFactory
from common.typings import Messages
from server.wfc_starter import start_wfc


class Server(ShowBase):
    def __init__(self):
        super().__init__(windowType="none")
        self.connection_manager = p3d.QueuedConnectionManager()
        self.connection_listener = p3d.QueuedConnectionListener(self.connection_manager, 0)
        self.connection_reader = p3d.QueuedConnectionReader(self.connection_manager, 0)
        self.connection_writer = p3d.ConnectionWriter(self.connection_manager, 0)
        self.active_connections = []
        self.node_path_factory = TileNodePathFactory(self.loader)
        print("[INFO] Starting WFC map generation")
        self.tiles, self.player_positions = start_wfc(10, 1)
        print("[INFO] Map generated")

    def listen(self, port):
        tcp_socket = self.connection_manager.open_TCP_server_rendezvous(port, 1000)
        self.connection_listener.add_connection(tcp_socket)
        taskMgr.add(self.poll_listener, "poll the connection listener", -39)
        taskMgr.add(self.poll_reader, "poll the connection reader", -40)
        print(f"[INFO] Server started on port {port}")

    def poll_listener(self, task):
        if self.connection_listener.new_connection_available():
            print("[INFO] New connection")
            rendezvous = p3d.PointerToConnection()
            net_address = p3d.NetAddress()
            new_connection = p3d.PointerToConnection()
            if self.connection_listener.get_new_connection(rendezvous, net_address, new_connection):
                new_connection = new_connection.p()
                self.active_connections.append(new_connection)
                self.connection_reader.add_connection(new_connection)
        return task.cont

    def poll_reader(self, task):
        if self.connection_reader.data_available():
            datagram = p3d.NetDatagram()
            if self.connection_reader.get_data(datagram):
                datagram_iterator = PyDatagramIterator(datagram)
                message = datagram_iterator.get_uint8()
                self.handle_message(message, datagram.get_connection())
        return task.cont

    def handle_message(self, message, origin_connection):
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
            self.connection_writer.send(datagram, origin_connection)


if __name__ == "__main__":
    server = Server()
    server.listen(os.environ.get("PORT", 7654))
    server.run()
