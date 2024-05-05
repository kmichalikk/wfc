import sys
import time
from typing import Callable
import panda3d.core as p3d

from direct.showbase.DirectObject import DirectObject
from direct.task.TaskManagerGlobal import taskMgr

from common.connection.udp_connection_thread import UDPConnectionThread
from common.state.game_config import GameConfig
from common.state.player_state_diff import PlayerStateDiff
from common.transfer.network_transfer import NetworkTransfer
from common.transfer.network_transfer_builder import NetworkTransferBuilder
from common.typings import Address, Messages


class ConnectionManager(DirectObject):
    """ Proxy for UDP connection thread """
    def __init__(self, server_address: Address, client):
        super().__init__()
        self.server_address = server_address
        self.client = client

        # set up class fields
        self.network_transfer_builder = NetworkTransferBuilder()
        self.ready_handler = lambda _: False
        self.game_state_change_subscriber = lambda _: False
        self.new_player_subscriber = lambda _: False
        self.game_end_subscriber = lambda _: False

        # initialize UDP thread
        self.udp_connection = UDPConnectionThread(server_address[0], 0)
        self.udp_connection.start()

        # say hello to server
        self.network_transfer_builder.add("type", Messages.HELLO)
        self.network_transfer_builder.set_destination(self.server_address)
        self.udp_connection.enqueue_transfer(self.network_transfer_builder.encode())

        self.room_found = False

        # begin processing of incoming messages
        taskMgr.add(self.process_messages, "process incoming transfers")

    def wait_for_connection(self, ready_handler: Callable[[GameConfig], None]):
        """ Add listener for server sending room information, send a room request """
        self.ready_handler = ready_handler

        def wait(task):
            if self.room_found:
                return

            self.network_transfer_builder.set_destination(self.server_address)
            self.network_transfer_builder.add("type", Messages.FIND_ROOM)
            self.udp_connection.enqueue_transfer(self.network_transfer_builder.encode())
            taskMgr.do_method_later(2, wait, 'wait for room')
        wait(None)

    def subscribe_for_game_state_change(self, subscriber: Callable[[NetworkTransfer], None]):
        self.game_state_change_subscriber = subscriber

    def subscribe_for_new_player(self, subscriber: Callable[[PlayerStateDiff], None]):
        self.new_player_subscriber = subscriber

    def subscribe_for_game_end(self, subscriber: Callable[[str], None]):
        self.game_end_subscriber = subscriber

    def send_input_update(self, input: str):
        self.network_transfer_builder.add("type", Messages.UPDATE_INPUT)
        self.network_transfer_builder.add("input", input)
        self.network_transfer_builder.add("timestamp", str(time.time()))
        self.network_transfer_builder.set_destination(self.server_address)
        self.udp_connection.enqueue_transfer(self.network_transfer_builder.encode())

    def send_gun_trigger(self, direction: p3d.Vec3, timestamp: int):
        self.network_transfer_builder.add("type", Messages.FIRE_GUN)
        self.network_transfer_builder.add("timestamp", timestamp)
        self.network_transfer_builder.add("x", direction.get_x())
        self.network_transfer_builder.add("y", direction.get_y())
        self.network_transfer_builder.set_destination(self.server_address)
        self.udp_connection.enqueue_transfer(self.network_transfer_builder.encode())

    def send_flag_trigger(self, player, timestamp: int):
        self.network_transfer_builder.add("type", Messages.FLAG_PICKED)
        self.network_transfer_builder.add("timestamp", timestamp)
        self.network_transfer_builder.add("player", player)
        self.network_transfer_builder.set_destination(self.server_address)
        self.udp_connection.enqueue_transfer(self.network_transfer_builder.encode())

    def send_flag_drop_trigger(self, player, timestamp: int):
        self.network_transfer_builder.add("type", Messages.FLAG_DROPPED)
        self.network_transfer_builder.add("timestamp", timestamp)
        self.network_transfer_builder.add("player", player)
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
                self.room_found = True
            elif type == Messages.FIND_ROOM_FAIL:
                print("[INFO] Server is full - 4/4 players. Access denied.")
                sys.exit()
            elif type == Messages.GLOBAL_STATE:
                self.game_state_change_subscriber(transfer)
            elif type == Messages.NEW_PLAYER:
                print("[INFO] New player")
                player_state = PlayerStateDiff.empty(transfer.get("id"))
                player_state.restore(transfer)
                self.new_player_subscriber(player_state)
            elif type == Messages.PLAYER_PICKED_FLAG:
                print("[INFO] Flag picked")
                self.client.player_flag_pickup(transfer.get("player"))
            elif type == Messages.PLAYER_DROPPED_FLAG:
                print("[INFO] Flag dropped")
                self.client.player_flag_drop(transfer.get("player"))
            elif type == Messages.GAME_END:
                print("[INFO] Game end")
                self.game_end_subscriber(str(transfer.get("id")))

        return task.cont
