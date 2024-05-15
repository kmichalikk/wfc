import pickle
from typing import Union

from common.transfer.network_transfer import NetworkTransfer
from common.typings import Address, SupportsBuildingNetworkTransfer


class NetworkTransferBuilder(SupportsBuildingNetworkTransfer):
    def __init__(self):
        self.data: dict[str, Union[str, int]] = {}
        self.destination = ("", 0)  # in form of ("127.0.0.1", 1234)
        self.source = ("", 0)

    def cleanup(self):
        self.data = {}
        self.destination = ("", 0)
        self.source = ("", 0)

    def add(self, key: str, value: Union[str, int]):
        self.data[key] = value

    def set_destination(self, address: Address):
        self.destination = address

    def set_source(self, address: Address):
        self.source = address

    def encode(self, reset=True, retransmit=1) -> NetworkTransfer:
        transfer = NetworkTransfer()
        transfer.payload = pickle.dumps(self.data)
        transfer.destination = self.destination
        if reset:
            self.cleanup()
        return transfer

    def decode(self, payload: bytes) -> NetworkTransfer:
        transfer = NetworkTransfer()
        transfer.data = pickle.loads(payload)
        transfer.source = self.source
        self.cleanup()
        return transfer
