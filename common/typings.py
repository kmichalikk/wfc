from abc import abstractmethod
from enum import IntEnum, auto
from typing import Literal, Protocol, TypeVar, NamedTuple, Union

Direction = Literal["n", "e", "s", "w"]

Input = Literal["+forward", "-forward", "+right", "-right", "+left", "-left", "+backward", "-backward"]

Item = Literal["flag", "empty"]

Address = tuple[Union[str, None], Union[int, None]]  # (address, port)


class Messages(IntEnum):
    HELLO = auto()
    KEEP_ALIVE = auto()
    FIND_ROOM = auto()
    FIND_ROOM_OK = auto()
    FIND_ROOM_FAIL = auto()
    LEAVE_ROOM = auto()
    GLOBAL_STATE = auto()
    UPDATE_INPUT = auto()
    FIRE_GUN = auto()
    NEW_PLAYER = auto()
    FLAG_PICKED = auto()
    PLAYER_DROPPED_FLAG = auto()
    PLAYER_PICKED_FLAG = auto()


class TimeStep(NamedTuple):
    begin: float
    end: float


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
