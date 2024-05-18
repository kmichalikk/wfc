from abc import abstractmethod
from enum import IntEnum, auto, StrEnum
from typing import Literal, Protocol, TypeVar, NamedTuple, Union

from common.collision.collision_object import CollisionObject

Direction = Literal["n", "e", "s", "w"]


class Input(StrEnum):
    PLUS_FORWARD = "+forward"
    MINUS_FORWARD = "-forward"
    PLUS_RIGHT = "+right"
    MINUS_RIGHT = "-right"
    PLUS_LEFT = "+left"
    MINUS_LEFT = "-left"
    PLUS_BACKWARD = "+backward"
    MINUS_BACKWARD = "-backward"


Item = Literal["flag", "empty"]

Address = tuple[Union[str, None], Union[int, None]]  # (address, port)

BulletMetadata = tuple[float, float, float, float]  # position x, y; direction x, y


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
    FLAG_DROPPED = auto()
    PLAYER_DROPPED_FLAG = auto()
    PLAYER_PICKED_FLAG = auto()
    PLAYER_TELEPORTED = auto()
    PLAYER_PICKED_BOLT = auto()
    BOLTS_UPDATE = auto()
    BOLTS_SETUP = auto()
    GAME_END = auto()
    FREEZE_PLAYER = auto()
    RESUME_PLAYER = auto()


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


class SupportsCollisionRegistration(Protocol):
    @abstractmethod
    def get_colliders(self) -> list[CollisionObject]:
        raise NotImplementedError()
