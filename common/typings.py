from abc import abstractmethod
from enum import IntEnum, auto
from typing import Literal, Protocol, TypeVar, NamedTuple, Union

Direction = Literal["n", "e", "s", "w"]

Input = Literal["+forward", "-forward", "+right", "-right", "+left", "-left", "+backward", "-backward"]

Item = Literal["flag", "empty"]

Address = tuple[Union[str, None], Union[int, None]]  # (address, port)


class Messages(IntEnum):
    HELLO = auto()
    HELLO_OK = auto()
    FIND_ROOM = auto()
    FIND_ROOM_OK = auto()
    ACCEPT_ROOM = auto()
    ACCEPT_ROOM_OK = auto()
    ACCEPT_ROOM_FAIL = auto()
    LEAVE_ROOM = auto()
    GLOBAL_STATE = auto()
    UPDATE_INPUT = auto()


class TimeStep(NamedTuple):
    begin: float
    end: float
    index: int


class SupportsBuildingNetworkTransfer(Protocol):
    @abstractmethod
    def add(self, key: str, value: Union[str, int]):
        raise NotImplementedError()

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

    @abstractmethod
    def restore(self, transfer):
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
