from typing import Union
from common.objects.bolt_factory import BoltFactory
from common.transfer.network_transfer import NetworkTransfer
from common.transfer.network_transfer_builder import NetworkTransferBuilder
from common.typings import Messages
from server.chain_of_responsibility.abstract_handler import AbstractHandler
from server.typings import HandlerContext, ServerGame


class BoltHandler(AbstractHandler):
    def __init__(self, bolt_factory: BoltFactory):
        super().__init__()
        self.server_game: Union[ServerGame, None] = None
        self.bolt_factory = bolt_factory
        self.network_transfer_builder = NetworkTransferBuilder()

    def handle(self, context: HandlerContext) -> list[NetworkTransfer]:
        if context.message != Messages.PLAYER_PICKED_BOLT:
            return self.pass_to_next(context)

        old_bolt_id = context.transfer.get('bolt_id')
        self.bolt_factory.remove_bolt(old_bolt_id)
        new_bolt = self.bolt_factory.add_bolt()
        self.network_transfer_builder.add("type", Messages.BOLTS_UPDATE)
        self.network_transfer_builder.add("old_bolt", old_bolt_id)
        self.network_transfer_builder.add("new_bolt", new_bolt)

        return self.repeat_for_all_addresses(
            context.known_addresses,
            self.network_transfer_builder
        )
