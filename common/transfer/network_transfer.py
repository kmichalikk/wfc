from typing import Union

from common.typings import Address


class NetworkTransfer:
    def __init__(self, data: dict[str, str], payload: bytes, address: Union[Address, None] = None):
        self.data: dict[str, str] = data
        self.payload: bytes = payload
        self.dst: Union[Address, None] = address

    def get(self, key: str) -> str:
        return self.data[key]

    def get_payload(self) -> bytes:
        return self.payload

    def get_destination(self) -> Address:
        return self.dst