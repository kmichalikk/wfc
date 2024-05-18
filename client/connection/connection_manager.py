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

    def __init__(self, server_address: Address):
        super().__init__()
        self.__server_address = server_address

        # set up class fields
        self.__network_transfer_builder = NetworkTransferBuilder()
        self.__ready_handler = lambda _: False

        # initialize UDP thread
        self.__udp_connection = UDPConnectionThread(server_address[0], 0)
        self.__udp_connection.start()

        # say hello to server
        self.__network_transfer_builder.add("type", Messages.HELLO)
        self.__network_transfer_builder.set_destination(self.__server_address)
        self.__udp_connection.enqueue_transfer(self.__network_transfer_builder.encode())
        self.__message_handlers = self.__get_message_handlers()
        self.__subscribers: dict[Messages, Callable[..., None]] = {}

        self.__room_found = False

        # begin processing of incoming messages
        taskMgr.add(self.process_messages, "process incoming transfers")

    def wait_for_connection(self, ready_handler: Callable[[GameConfig], None], username):
        """ Add listener for server sending room information, send a room request """
        self.__ready_handler = ready_handler

        def wait(task):
            if self.__room_found:
                return

            self.__network_transfer_builder.set_destination(self.__server_address)
            self.__network_transfer_builder.add("type", Messages.FIND_ROOM)
            self.__network_transfer_builder.add("username", username)
            self.__udp_connection.enqueue_transfer(self.__network_transfer_builder.encode())
            taskMgr.do_method_later(2, wait, 'wait for room')

        wait(None)

    def on(self, message_type: Messages, handler: Callable[..., None]):
        self.__subscribers[message_type] = handler

    def dispatch(self, message_type: Messages, *args):
        self.__subscribers[message_type](*args)

    def send_input_update(self, input: str):
        self.__network_transfer_builder.add("type", Messages.UPDATE_INPUT)
        self.__network_transfer_builder.add("input", input)
        self.__network_transfer_builder.add("timestamp", str(time.time()))
        self.__network_transfer_builder.set_destination(self.__server_address)
        self.__udp_connection.enqueue_transfer(self.__network_transfer_builder.encode())

    def send_gun_trigger(self, direction: p3d.Vec3, timestamp: int):
        self.__network_transfer_builder.add("type", Messages.FIRE_GUN)
        self.__network_transfer_builder.add("timestamp", timestamp)
        self.__network_transfer_builder.add("x", direction.get_x())
        self.__network_transfer_builder.add("y", direction.get_y())
        self.__network_transfer_builder.set_destination(self.__server_address)
        self.__udp_connection.enqueue_transfer(self.__network_transfer_builder.encode())

    def send_flag_trigger(self, player):
        self.__network_transfer_builder.add("type", Messages.FLAG_PICKED)
        self.__network_transfer_builder.add("player", player)
        self.__network_transfer_builder.set_destination(self.__server_address)
        self.__udp_connection.enqueue_transfer(self.__network_transfer_builder.encode())

    def send_flag_drop_trigger(self, player):
        self.__network_transfer_builder.add("type", Messages.FLAG_DROPPED)
        self.__network_transfer_builder.add("player", player)
        self.__network_transfer_builder.set_destination(self.__server_address)
        self.__udp_connection.enqueue_transfer(self.__network_transfer_builder.encode())

    def send_bolt_pickup_trigger(self, bolt_id: str):
        self.__network_transfer_builder.add("type", Messages.PLAYER_PICKED_BOLT)
        self.__network_transfer_builder.add("bolt_id", bolt_id)
        self.__network_transfer_builder.set_destination(self.__server_address)
        self.__udp_connection.enqueue_transfer(self.__network_transfer_builder.encode())

    def send_freeze_trigger(self, player):
        self.__network_transfer_builder.add("type", Messages.FREEZE_PLAYER)
        self.__network_transfer_builder.add("player", player)
        self.__network_transfer_builder.set_destination(self.__server_address)
        self.__udp_connection.enqueue_transfer(self.__network_transfer_builder.encode())

    def process_messages(self, task):
        for transfer in self.__udp_connection.get_queued_transfers():
            self.__message_handlers[Messages(transfer.get("type"))](transfer)

        return task.cont

    def __get_message_handlers(self) -> dict[Messages, Callable[[NetworkTransfer], None]]:
        return {
            Messages.FIND_ROOM_OK: self.__handle_room_found,
            Messages.FIND_ROOM_FAIL: self.__handle_room_not_found,
            Messages.GLOBAL_STATE: self.__handle_global_state,
            Messages.NEW_PLAYER: self.__handle_new_player,
            Messages.PLAYER_PICKED_FLAG: self.__handle_flag_pickup,
            Messages.PLAYER_DROPPED_FLAG: self.__handle_flag_drop,
            Messages.GAME_END: self.__handle_game_end,
            Messages.BOLTS_SETUP: self.__handle_bolts_setup,
            Messages.BOLTS_UPDATE: self.__handle_bolts_update,
            Messages.RESUME_PLAYER: self.__handle_resume_player
        }

    def __handle_resume_player(self, _: NetworkTransfer):
        print("[INFO] Energy recharged")
        self.dispatch(Messages.RESUME_PLAYER)

    def __handle_bolts_update(self, transfer: NetworkTransfer):
        self.dispatch(Messages.BOLTS_UPDATE, transfer.get("old_bolt"), transfer.get("new_bolt"))

    def __handle_bolts_setup(self, transfer: NetworkTransfer):
        self.dispatch(Messages.BOLTS_SETUP, transfer.get("current_bolts"))

    def __handle_game_end(self, transfer: NetworkTransfer):
        print("[INFO] Game end")
        self.dispatch(Messages.GAME_END, str(transfer.get("id")), transfer.get("username"),
                      int(transfer.get("wins")), int(transfer.get("losses")))

    def __handle_flag_drop(self, transfer: NetworkTransfer):
        print("[INFO] Flag dropped")
        self.dispatch(Messages.PLAYER_DROPPED_FLAG, transfer.get("player"))

    def __handle_flag_pickup(self, transfer: NetworkTransfer):
        print("[INFO] Flag picked")
        self.dispatch(Messages.PLAYER_PICKED_FLAG, transfer.get("player"))

    def __handle_new_player(self, transfer: NetworkTransfer):
        print("[INFO] New player")
        player_state = PlayerStateDiff.empty(transfer.get("id"))
        player_state.restore(transfer)
        self.dispatch(Messages.NEW_PLAYER, player_state)

    def __handle_global_state(self, transfer: NetworkTransfer):
        self.dispatch(Messages.GLOBAL_STATE, transfer)

    def __handle_room_not_found(self, _: NetworkTransfer):
        print("[INFO] Server is full - 4/4 players. Access denied.")
        sys.exit()

    def __handle_room_found(self, transfer: NetworkTransfer):
        print("[INFO] Room found")
        game_config = GameConfig.empty()
        game_config.restore(transfer)
        self.__ready_handler(game_config)
        self.__room_found = True
