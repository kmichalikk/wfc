from typing import Union

from common.typings import Address


class NetworkTransfer:
    def __init__(self):
        self.data: dict[str, Union[str, int]] = {}
        self.payload: bytes = b""
        self.destination: Address = (None, None)
        self.source: Address = (None, None)

    def get(self, key: str) -> Union[str, int]:
        return self.data[key]

    def get_payload(self) -> bytes:
        return self.payload

    def get_destination(self) -> Address:
        return self.destination

    def get_source(self) -> Address:
        return self.source
