from typing import Callable
from common.transfer.network_transfer import NetworkTransfer
from common.typings import Address, Messages
from server.chain_of_responsibility.abstract_handler import AbstractHandler
from server.typings import HandlerContext


class FreezePlayerHandler(AbstractHandler):
    def __init__(self, freeze_handler: Callable[[Address], None]):
        super().__init__()
        self.freeze_handler = freeze_handler

    def handle(self, context: HandlerContext) -> list[NetworkTransfer]:
        if context.message != Messages.FREEZE_PLAYER:
            return self.pass_to_next(context)

        transfer = context.get_transfer()
        address = transfer.get_source()
        self.freeze_handler(address)

        return []
