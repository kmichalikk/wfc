import sys
from direct.showbase.ShowBase import ShowBase

from common.tiles.tile_node_path_factory import TileNodePathFactory
from common.connection.udp_connection_thread import UDPConnectionThread
from server.wfc.wfc_starter import start_wfc

sys.path.append("../common")


class Server(ShowBase):
    def __init__(self, address, port):
        super().__init__(windowType="none")
        self.port = port
        self.udp_connection = UDPConnectionThread(address, port)
        self.node_path_factory = TileNodePathFactory(self.loader)
        print("[INFO] Starting WFC map generation")
        self.tiles, self.player_positions = start_wfc(10, 1)
        print("[INFO] Map generated")

    def listen(self):
        self.udp_connection.start()
        print(f"[INFO] Listening on port {self.port}")


if __name__ == "__main__":
    server = Server('127.0.0.1', 7654)
    server.set_sleep(0.016)
    server.listen()
    print(f"[INFO] Starting game loop")
    server.run()
