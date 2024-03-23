from enum import IntEnum, auto
from typing import Literal

Direction = Literal["n", "e", "s", "w"]

Input = Literal["+forward", "-forward", "+right", "-right", "+left", "-left", "+backward", "-backward"]


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
