from abc import abstractmethod
from typing import Literal, Protocol, TypeVar, NamedTuple

Direction = Literal["n", "e", "s", "w"]

Input = Literal["+forward", "-forward", "+right", "-right", "+left", "-left", "+backward", "-backward"]

Item = Literal["flag", "empty"]

Address = tuple[str, int]  # (address, port)


class Step(NamedTuple):
    begin: int
    end: int
    index: int


class SupportsBuildingNetworkTransfer(Protocol):
    @abstractmethod
    def encode(self):
        raise NotImplementedError()

    @abstractmethod
    def decode(self, payload: bytes):
        raise NotImplementedError()


class SupportsNetworkTransfer(Protocol):
    @abstractmethod
    def transfer(self, builder: SupportsBuildingNetworkTransfer):
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
