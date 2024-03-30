from typing import Callable

from direct.showbase.DirectObject import DirectObject
from direct.task.TaskManagerGlobal import taskMgr

from common.config.game_config import GameConfig
from common.connection.udp_connection_thread import UDPConnectionThread
from common.state.player_state_diff import PlayerStateDiff
from common.transfer.network_transfer import NetworkTransfer
from common.transfer.network_transfer_builder import NetworkTransferBuilder
from common.typings import Address, Messages


class ConnectionManager(DirectObject):
    def __init__(self, server_address: Address):
        super().__init__()
        self.server_address = server_address
        self.udp_connection = UDPConnectionThread(server_address[0], 0)
        self.udp_connection.start()
        self.network_transfer_builder = NetworkTransferBuilder()
        self.network_transfer_builder.add("type", Messages.HELLO)
        self.network_transfer_builder.set_destination(self.server_address)
        self.udp_connection.enqueue_transfer(self.network_transfer_builder.encode())
        self.ready_handler = lambda _: False
        self.game_state_change_subscriber = lambda _: False
        self.new_player_subscriber = lambda _: False
        taskMgr.add(self.process_messages, "process incoming transfers")

    def wait_for_connection(self, ready_handler: Callable[[GameConfig], None]):
        self.ready_handler = ready_handler
        self.network_transfer_builder.set_destination(self.server_address)
        self.network_transfer_builder.add("type", Messages.FIND_ROOM)
        self.udp_connection.enqueue_transfer(self.network_transfer_builder.encode())

    def subscribe_for_game_state_change(self, subscriber: Callable[[NetworkTransfer], None]):
        self.game_state_change_subscriber = subscriber

    def subscribe_for_new_player(self, subscriber: Callable[[PlayerStateDiff], None]):
        self.new_player_subscriber = subscriber

    def send_input_update(self, input: str):
        self.network_transfer_builder.add("type", Messages.UPDATE_INPUT)
        self.network_transfer_builder.add("input", input)
        self.network_transfer_builder.set_destination(self.server_address)
        self.udp_connection.enqueue_transfer(self.network_transfer_builder.encode())

    def process_messages(self, task):
        for transfer in self.udp_connection.get_queued_transfers():
            type = transfer.get("type")
            if type == Messages.FIND_ROOM_OK:
                print("[INFO] Room found")
                game_config = GameConfig.empty()
                game_config.restore(transfer)
                self.ready_handler(game_config)
            elif type == Messages.GLOBAL_STATE:
                self.game_state_change_subscriber(transfer)
            elif type == Messages.NEW_PLAYER:
                player_state = PlayerStateDiff.empty(transfer.get("id"))
                player_state.restore(transfer)
                self.new_player_subscriber(player_state)

        return task.cont
