from typing import Union

import simplepbr

from direct.showbase.ShowBase import ShowBase

from client.builder import setup_map, setup_player
from client.connection.connection_manager import ConnectionManager
from client.player.player_controller import PlayerController
from common.typings import Input
from server.wfc.wfc_starter import start_wfc


class Game(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)

        self.map_size = 10
        self.players_count = 4
        self.player: Union[PlayerController, None] = None
        self.connection_manager = ConnectionManager(('127.0.0.1', 7654))

        simplepbr.init()

        tiles, player_positions = start_wfc(self.map_size, self.players_count)

        setup_map(self, tiles)
        setup_player(self, player_positions)

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
