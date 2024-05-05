import time

import simplepbr

from direct.showbase.ShowBase import ShowBase
from direct.showbase.ShowBaseGlobal import globalClock, aspect2d
from panda3d.core import ClockObject, PStatClient, load_prc_file_data

from client.game_manager import GameManager
from client.connection.connection_manager import ConnectionManager
from client.connection.login_screen import LoginScreen

from common.config import FRAMERATE, SERVER_ADDRESS, SERVER_PORT
from common.objects.bolt_factory import BoltFactory
from common.objects.flag import Flag
from common.state.game_config import GameConfig
from common.state.player_state_diff import PlayerStateDiff
from common.tiles.tile_node_path_factory import TileNodePathFactory
from common.transfer.network_transfer import NetworkTransfer
from common.typings import Input


load_prc_file_data("", """
sync-video 0
yield-timeslice 0
client-sleep 0
multi-sleep 0
""")


class Game(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)
        # proper textures & lighting
        simplepbr.init()

        aspect2d.set_transparency(True)

        # initialize ConnectionManager and subscribe to all event it handles
        self.connection_manager = ConnectionManager((SERVER_ADDRESS, SERVER_PORT), self)
        self.login_screen = LoginScreen(self.loader, self.start)

        # initialize GameManager, don't start the game until self.ready
        self.game_manager = GameManager(self, TileNodePathFactory(self.loader))
        self.flag = Flag(self)

        self.bolt_factory = BoltFactory(self.loader, self.render)

    def start(self, username):
        self.connection_manager.wait_for_connection(self.ready_handler, username)
        self.connection_manager.subscribe_for_new_player(self.new_player_handler)
        self.connection_manager.subscribe_for_game_end(self.game_manager.game_end_handler)

    def ready_handler(self, game_config: GameConfig):
        self.expected_players = game_config.expected_players
        self.game_manager.setup_map(self, game_config.tiles, game_config.size, game_config.season)
        for state in game_config.player_states:
            player = self.game_manager.setup_player(state)
            if state.id == game_config.id:
                self.game_manager.set_main_player(player)

        # now the game is ready to start, so we start listening for server changes
        self.connection_manager.subscribe_for_new_player(self.new_player_handler)
        self.connection_manager.subscribe_for_game_state_change(self.game_state_change)

    def game_state_change(self, game_state_transfer: NetworkTransfer):
        self.game_manager.queue_server_game_state(game_state_transfer)

    def new_player_handler(self, player_state: PlayerStateDiff):
        print("[INFO] New player {}".format(player_state.username))
        self.game_manager.setup_player(player_state)

    def attach_input(self):
        self.accept("w", lambda: self.handle_input("+forward"))
        self.accept("w-up", lambda: self.handle_input("-forward"))
        self.accept("s", lambda: self.handle_input("+backward"))
        self.accept("s-up", lambda: self.handle_input("-backward"))
        self.accept("d", lambda: self.handle_input("+right"))
        self.accept("d-up", lambda: self.handle_input("-right"))
        self.accept("a", lambda: self.handle_input("+left"))
        self.accept("a-up", lambda: self.handle_input("-left"))
        self.accept("space-up", lambda: self.handle_bullet())
        self.accept("q", lambda: self.handle_flag_drop())

    def detach_input(self):
        keys = ["w", "w-up", "s", "s-up", "d", "d-up", "a", "a-up"]
        for key in keys:
            self.accept(key, lambda: self.handle_input("stop"))

    def handle_bullet(self):
        direction = self.game_manager.shoot_bullet()
        timestamp = int(time.time()*1000)
        self.taskMgr.do_method_later(0, lambda _: self.connection_manager.send_gun_trigger(direction, timestamp),
                                     "send input on next frame")

    def handle_flag(self, player, entry):
        self.taskMgr.do_method_later(0, lambda _: self.connection_manager.send_flag_trigger(player.get_id()),
                                     "send input on next frame")

    def handle_flag_drop(self):
        player = self.game_manager.main_player
        self.taskMgr.do_method_later(0, lambda _: self.connection_manager.send_flag_drop_trigger(player.get_id()),
                                     "send input on next frame")

    def player_flag_pickup(self, id):
        player = self.game_manager.players[id]
        self.flag.get_picked(player)

    def player_flag_drop(self, id):
        player = self.game_manager.players[id]
        self.flag.get_dropped(player)

    def setup_bolts(self, current_bolts):
        self.bolt_factory.copy_bolts(current_bolts)

    def update_bolts(self, old_bolt_id, new_bolt):
        self.bolt_factory.remove_bolt(old_bolt_id)
        self.bolt_factory.copy_bolts([new_bolt])

    def pick_bolt(self, entry):
        bolt_id = entry.getIntoNodePath().node().getName()[-1]
        player_id = entry.getFromNodePath().node().getName()[-1]
        player = self.game_manager.players[player_id]
        player.charge_energy()
        self.taskMgr.do_method_later(0, lambda _: self.connection_manager.send_bolt_pickup_trigger(bolt_id),
                                     "send input on next frame")

    def handle_input(self, input: Input):
        self.game_manager.main_player.update_input(input)
        # send input to server on next frame in order to give ourselves a change
        # to respond to input before server sees it
        # otherwise, we would get server response on localhost before we'd processed it locally
        self.taskMgr.do_method_later(0, lambda _: self.connection_manager.send_input_update(input),
                                     "send input on next frame")


if __name__ == "__main__":
    game = Game()
    globalClock.setMode(ClockObject.MLimited)
    globalClock.setFrameRate(FRAMERATE)
    # PStatClient.connect()
    game.run()
