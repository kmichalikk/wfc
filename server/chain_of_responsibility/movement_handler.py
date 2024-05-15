from typing import Union
from common.transfer.network_transfer import NetworkTransfer
from common.typings import Input, Messages
from server.chain_of_responsibility.abstract_handler import AbstractHandler
from server.typings import HandlerContext, ServerGame


class MovementHandler(AbstractHandler):
    def __init__(self, game: ServerGame):
        super().__init__()
        self.game = game

    def handle(self, context: HandlerContext) -> list[NetworkTransfer]:
        if context.message != Messages.UPDATE_INPUT:
            return self.pass_to_next(context)

        active_players = self.game.get_active_players()
        transfer = context.get_transfer()
        if transfer.get_source() not in active_players:
            return []

        player_input = Input(str(transfer.get('input')))
        active_players[transfer.get_source()].update_input(player_input)

        return []
