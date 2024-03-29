import simplepbr

from direct.showbase.ShowBase import ShowBase

from client.builder import setup_map, setup_player
from client.player.player_controller import PlayerController
from server.wfc.wfc_starter import start_wfc


class Game(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)

        self.map_size = 10
        self.players_count = 4

        simplepbr.init()

        tiles, player_positions = start_wfc(self.map_size, self.players_count)

        setup_map(self, tiles)
        setup_player(self, player_positions)

        player_collider = self.player.colliders[0]
        self.cTrav.addCollider(player_collider, self.pusher)
        self.pusher.addCollider(player_collider, player_collider)
        self.pusher.setHorizontal(True)

    def attach_input(self, player: PlayerController):
        self.accept("w", lambda: player.motion.update_input("+forward"))
        self.accept("w-up", lambda: player.motion.update_input("-forward"))
        self.accept("s", lambda: player.motion.update_input("+backward"))
        self.accept("s-up", lambda: player.motion.update_input("-backward"))
        self.accept("d", lambda: player.motion.update_input("+right"))
        self.accept("d-up", lambda: player.motion.update_input("-right"))
        self.accept("a", lambda: player.motion.update_input("+left"))
        self.accept("a-up", lambda: player.motion.update_input("-left"))
