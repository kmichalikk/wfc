from typing import Union
from common.transfer.network_transfer import NetworkTransfer
from common.transfer.network_transfer_builder import NetworkTransferBuilder
from common.typings import Messages
from server.chain_of_responsibility.abstract_handler import AbstractHandler
from server.typings import HandlerContext, ServerGame


class ExistingClientHandler(AbstractHandler):
    """
    If existing player tries to find room, do not add the player again,
    but send game config of the current game
    """

    def __init__(self, game: ServerGame):
        super().__init__()
        self.game = game
        self.network_transfer_builder = NetworkTransferBuilder()

    def handle(self, context: HandlerContext) -> list[NetworkTransfer]:
        if context.message != Messages.FIND_ROOM:
            return self.pass_to_next(context)

        active_players = self.game.get_active_players()
        transfer = context.get_transfer()
        address = transfer.get_source()
        if address not in active_players:
            return self.pass_to_next(context)

        player_controller = active_players[transfer.get_source()]
        print(f"  --   Resending to player {player_controller.get_id()}")
        self.network_transfer_builder.add("id", player_controller.get_id())
        self.network_transfer_builder.set_destination(address)
        self.network_transfer_builder.add("type", Messages.FIND_ROOM_OK)
        self.game.get_game_config(player_controller.get_id()) \
            .transfer(self.network_transfer_builder)

        return [self.network_transfer_builder.encode()]
