from abc import abstractmethod
from dataclasses import dataclass
from typing import Protocol

from common.objects.bullet import Bullet
from common.player.player_controller import PlayerController
from common.state.game_config import GameConfig
from common.transfer.network_transfer import NetworkTransfer
from common.typings import Address, Messages


class ServerGame(Protocol):
    @abstractmethod
    def get_active_players(self) -> dict[Address, PlayerController]:
        raise NotImplementedError()

    @abstractmethod
    def add_projectile_to_process(self, bullet: Bullet):
        raise NotImplementedError()

    @abstractmethod
    def get_game_config(self, player_id: str) -> GameConfig:
        raise NotImplementedError()


@dataclass
class HandlerContext:
    message: Messages
    transfer: NetworkTransfer
    known_addresses: list[Address]

    def get_transfer(self) -> NetworkTransfer:
        return self.transfer


class SupportsServerOperationsChain(Protocol):
    @abstractmethod
    def set_next(self, next_in_chain: 'SupportsServerOperationsChain'):
        raise NotImplementedError()

    @abstractmethod
    def handle(self, context: HandlerContext) -> list[NetworkTransfer]:
        raise NotImplementedError()
