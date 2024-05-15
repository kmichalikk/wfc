from common.objects.flag import Flag
from common.transfer.network_transfer import NetworkTransfer
from common.transfer.network_transfer_builder import NetworkTransferBuilder
from common.typings import Messages
from server.chain_of_responsibility.abstract_handler import AbstractHandler
from server.typings import HandlerContext, ServerGame


class FlagHandler(AbstractHandler):
    def __init__(self, flag: Flag, game: ServerGame):
        super().__init__()
        self.flag = flag
        self.game = game
        self.network_transfer_builder = NetworkTransferBuilder()

    def handle(self, context: HandlerContext) -> list[NetworkTransfer]:

        if context.message == Messages.FLAG_PICKED:
            return self.__handle_flag_pickup(context)
        elif context.message == Messages.FLAG_DROPPED:
            return self.__handle_flag_drop(context)
        else:
            return self.pass_to_next(context)

    def __handle_flag_pickup(self, context: HandlerContext) -> list[NetworkTransfer]:
        if self.flag.taken():
            return []

        transfer = context.get_transfer()
        player_address, player_id = transfer.get_source(), str(transfer.get("player"))

        print("[INFO] Flag picked by player " + player_id)
        self.flag.get_picked(self.game.get_active_players()[player_address])

        self.network_transfer_builder.add("type", Messages.PLAYER_PICKED_FLAG)
        self.network_transfer_builder.add("player", player_id)

        return self.repeat_for_all_addresses(
            context.known_addresses,
            self.network_transfer_builder
        )

    def __handle_flag_drop(self, context: HandlerContext) -> list[NetworkTransfer]:
        transfer = context.get_transfer()
        player_address, player_id = transfer.get_source(), str(transfer.get("player"))

        if not self.flag.taken() or player_id != self.flag.get_player_id():
            return []

        print("[INFO] Flag dropped by player " + player_id)
        self.flag.get_dropped(self.game.get_active_players()[player_address])

        self.network_transfer_builder.add("type", Messages.PLAYER_DROPPED_FLAG)
        self.network_transfer_builder.add("player", player_id)

        return self.repeat_for_all_addresses(
            context.known_addresses,
            self.network_transfer_builder
        )
