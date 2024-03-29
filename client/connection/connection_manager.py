from typing import Callable

from common.config.game_config import GameConfig
from common.config.player_config import PlayerConfig
from common.connection.udp_connection_thread import UDPConnectionThread
from common.state.game_state_diff import GameStateDiff
from common.transfer.network_transfer_builder import NetworkTransferBuilder
from common.typings import Address


class ConnectionManager:
    def __init__(self, server_address: Address):
        self.server_address = server_address
        self.udp_connection = UDPConnectionThread(server_address[0], 0)
        self.udp_connection.start()
        self.network_transfer_builder = NetworkTransferBuilder()

    def wait_for_connection(self, ready_handler: Callable[[GameConfig], None]):
        pass

    def subscribe_for_game_state_change(self, subscriber: Callable[[GameStateDiff], None]):
        pass

    def subscribe_for_new_player(self, subscriber: Callable[[PlayerConfig], None]):
        pass

    def send_input_update(self, input: str):
        self.network_transfer_builder.add("input", input)
        self.network_transfer_builder.set_destination(self.server_address)
        self.udp_connection.enqueue_message(self.network_transfer_builder.encode())
