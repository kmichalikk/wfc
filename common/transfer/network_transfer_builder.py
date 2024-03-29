import pickle

from common.transfer.network_transfer import NetworkTransfer
from common.typings import Address, SupportsBuildingNetworkTransfer


class NetworkTransferBuilder(SupportsBuildingNetworkTransfer):
    def __init__(self):
        self.data: dict[str, str] = {}
        self.address = ("", 0)

    def __cleanup(self):
        self.timestamp = 0.0
        self.data = {}

    def add(self, key: str, value: str):
        self.data[key] = value

    def set_destination(self, address: Address):
        self.address = address

    def encode(self) -> NetworkTransfer:
        transfer = NetworkTransfer(
            self.data,
            pickle.dumps(self.data),
            self.address
        )
        self.__cleanup()

        return transfer

    def decode(self, payload: bytes) -> NetworkTransfer:
        transfer = NetworkTransfer(
            pickle.loads(payload),
            payload,
        )
        self.__cleanup()

        return transfer
