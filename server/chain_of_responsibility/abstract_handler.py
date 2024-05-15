from typing import Union
from common.transfer.network_transfer import NetworkTransfer
from common.transfer.network_transfer_builder import NetworkTransferBuilder
from common.typings import Address
from server.typings import HandlerContext, SupportsServerOperationsChain


class AbstractHandler(SupportsServerOperationsChain):
    def __init__(self):
        self.next: Union[SupportsServerOperationsChain, None] = None

    def set_next(self, next_in_chain: 'SupportsServerOperationsChain'):
        self.next = next_in_chain

    def pass_to_next(self, context: HandlerContext) -> list[NetworkTransfer]:
        if self.next is not None:
            return self.next.handle(context)

        return []

    def repeat_for_all_addresses(
            self,
            addresses: list[Address],
            network_transfer_builder: NetworkTransferBuilder
    ) -> list[NetworkTransfer]:
        transfers = []
        for address in addresses:
            network_transfer_builder.set_destination(address)
            transfers.append(network_transfer_builder.encode(reset=False))
        network_transfer_builder.cleanup()
        return transfers
