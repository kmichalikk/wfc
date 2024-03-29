from typing import Union

import simplepbr

from direct.showbase.ShowBase import ShowBase

from client.builder import setup_map, setup_player
from client.connection.connection_manager import ConnectionManager
from common.config.game_config import GameConfig
from common.player.player_controller import PlayerController
from common.typings import Input

class Game(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)
        simplepbr.init()

        self.map_size = 10
        self.players_count = 4
        self.player: Union[PlayerController, None] = None
        self.connection_manager = ConnectionManager(('127.0.0.1', 7654))
        self.connection_manager.wait_for_connection(self.ready_handler)

    def ready_handler(self, game_config: GameConfig):
        setup_map(self, game_config.tiles)
        setup_player(self, game_config.player_position)

        player_collider = self.player.colliders[0]
        self.cTrav.addCollider(player_collider, self.pusher)
        self.pusher.addCollider(player_collider, player_collider)
        self.pusher.setHorizontal(True)

    def attach_input(self):
        self.accept("w", lambda: self.handle_input("+forward"))
        self.accept("w-up", lambda: self.handle_input("-forward"))
        self.accept("s", lambda: self.handle_input("+backward"))
        self.accept("s-up", lambda: self.handle_input("-backward"))
        self.accept("d", lambda: self.handle_input("+right"))
        self.accept("d-up", lambda: self.handle_input("-right"))
        self.accept("a", lambda: self.handle_input("+left"))
        self.accept("a-up", lambda: self.handle_input("-left"))

    def handle_input(self, input: Input):
        if self.player is not None:
            self.player.update_input(input)
            self.connection_manager.send_input_update(input)
