from typing import Callable
from common.objects.bolt_factory import BoltFactory
from common.objects.flag import Flag
from common.transfer.network_transfer import NetworkTransfer
from common.transfer.network_transfer_builder import NetworkTransferBuilder
from common.typings import Address, Messages
from server.accounts.db_manager import DBManager
from server.chain_of_responsibility.abstract_handler import AbstractHandler
from server.typings import HandlerContext, ServerGame


class NewClientHandler(AbstractHandler):
    def __init__(
            self,
            game: ServerGame,
            adder: Callable[[Address, str], str],
            flag: Flag,
            bolt_factory: BoltFactory,
            db_manager: DBManager
    ):
        super().__init__()
        self.game = game
        self.adder = adder
        self.flag = flag
        self.bolt_factory = bolt_factory
        self.db_manager = db_manager
        self.network_transfer_builder = NetworkTransferBuilder()

    def handle(self, context: HandlerContext) -> list[NetworkTransfer]:
        if context.message != Messages.FIND_ROOM:
            return self.pass_to_next(context)

        active_players = self.game.get_active_players()
        transfer = context.get_transfer()
        address = transfer.get_source()
        if address in active_players:
            return self.pass_to_next(context)

        if len(active_players) >= 4:
            self.network_transfer_builder.set_destination(address)
            self.network_transfer_builder.add("type", Messages.FIND_ROOM_FAIL)
            return [self.network_transfer_builder.encode()]

        print("  --   Adding new player")
        new_player_id = self.adder(address, str(transfer.get("username")))

        new_player_transfers = [
            self.__get_new_player_config_transfer(address, new_player_id)
        ]

        new_player_transfers = self.__add_picked_flag(address, new_player_transfers)
        new_player_transfers = self.__add_bolts(address, new_player_transfers)
        self.db_manager.login(str(transfer.get("username")))

        active_players = self.game.get_active_players()

        print("[INFO] Notifying players about new player")
        self.network_transfer_builder.add("type", Messages.NEW_PLAYER)
        self.network_transfer_builder.add("id", new_player_id)
        active_players[address] \
            .get_state() \
            .transfer(self.network_transfer_builder)

        return new_player_transfers \
            + self.repeat_for_all_addresses(
                [addr for addr in context.known_addresses if addr != address],
                self.network_transfer_builder
            )

    def __get_new_player_config_transfer(
            self,
            address: Address,
            new_player_id: str
    ) -> NetworkTransfer:
        self.network_transfer_builder.add("id", str(new_player_id))
        self.network_transfer_builder.set_destination(address)
        self.network_transfer_builder.add("type", Messages.FIND_ROOM_OK)
        self.game.get_game_config(new_player_id) \
            .transfer(self.network_transfer_builder)
        return self.network_transfer_builder.encode()

    def __add_picked_flag(
            self,
            address: Address,
            transfers: list[NetworkTransfer],
    ) -> list[NetworkTransfer]:
        player_with_flag_id = self.flag.get_player_id()
        if player_with_flag_id:
            self.network_transfer_builder.set_destination(address)
            self.network_transfer_builder.add("type", Messages.PLAYER_PICKED_FLAG)
            self.network_transfer_builder.add("player", player_with_flag_id)
            transfers.append(self.network_transfer_builder.encode())

        return transfers

    def __add_bolts(
            self,
            address: Address,
            transfers: list[NetworkTransfer]
    ) -> list[NetworkTransfer]:
        self.network_transfer_builder.set_destination(address)
        self.network_transfer_builder.add("type", Messages.BOLTS_SETUP)
        self.network_transfer_builder.add("current_bolts", self.bolt_factory.dump_bolts())
        transfers.append(self.network_transfer_builder.encode(retransmit=5))

        return transfers
