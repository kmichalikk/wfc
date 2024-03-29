from abc import abstractmethod
from typing import Literal, Protocol, TypeVar, NamedTuple

from common.transfer.network_transfer_builder import NetworkTransferBuilder

Direction = Literal["n", "e", "s", "w"]

Input = Literal["+forward", "-forward", "+right", "-right", "+left", "-left", "+backward", "-backward"]

Item = Literal["flag", "empty"]


class Step(NamedTuple):
    begin: int
    end: int
    index: int


class SupportsNetworkTransfer(Protocol):
    @abstractmethod
    def transfer(self, builder: NetworkTransferBuilder):
        raise NotImplementedError()


# to support self reference in implementing classes
SD = TypeVar('SD', bound='SupportsDiff')


class SupportsDiff(Protocol):
    @abstractmethod
    def diff(self, other: 'SD') -> 'SD':
        raise NotImplementedError()

    @abstractmethod
    def apply(self, other: 'SD'):
        raise NotImplementedError()
