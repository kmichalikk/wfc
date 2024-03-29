import sys
from direct.showbase.ShowBase import ShowBase
from direct.task.TaskManagerGlobal import taskMgr

from common.config.game_config import GameConfig
from common.tiles.tile_node_path_factory import TileNodePathFactory
from common.connection.udp_connection_thread import UDPConnectionThread
from common.transfer.network_transfer_builder import NetworkTransferBuilder
from common.typings import Messages
from server.wfc.wfc_starter import start_wfc

sys.path.append("../common")


class Server(ShowBase):
    def __init__(self, address, port):
        super().__init__(windowType="none")
        self.port = port
        self.udp_connection = UDPConnectionThread(address, port)
        self.node_path_factory = TileNodePathFactory(self.loader)
        self.network_transfer_builder = NetworkTransferBuilder()
        print("[INFO] Starting WFC map generation")
        self.tiles, self.player_positions = start_wfc(10, 1)
        print("[INFO] Map generated")

    def listen(self):
        self.udp_connection.start()
        taskMgr.add(self.handle_clients, "handle client messages")
        print(f"[INFO] Listening on port {self.port}")

    def handle_clients(self, task):
        for transfer in self.udp_connection.get_queued_transfers():
            type = transfer.get("type")
            if type == Messages.HELLO:
                print("[INFO] New client")
            elif type == Messages.FIND_ROOM:
                print("[INFO] Room requested")
                self.network_transfer_builder.set_destination(transfer.get_source())
                self.network_transfer_builder.add("type", Messages.FIND_ROOM_OK)
                game_config = GameConfig(self.tiles, self.player_positions[0])
                game_config.transfer(self.network_transfer_builder)
                self.udp_connection.enqueue_transfer(self.network_transfer_builder.encode())
            elif type == Messages.UPDATE_INPUT:
                print("[INFO] Update input")
        return task.cont


if __name__ == "__main__":
    server = Server('127.0.0.1', 7654)
    server.set_sleep(0.016)
    server.listen()
    print(f"[INFO] Starting game loop")
    server.run()
