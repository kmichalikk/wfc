import time
from direct.task.TaskManagerGlobal import taskMgr
from direct.showbase.ShowBaseGlobal import globalClock
from panda3d.core import ClockObject, load_prc_file_data

from client.game import Game
from client.game_manager import GameManager
from client.connection.connection_manager import ConnectionManager
from client.screens.end_screen import EndScreen
from client.screens.login_screen import LoginScreen
from client.screens.waiting_screen import WaitingScreen

from common.config import FRAMERATE, SERVER_ADDRESS, SERVER_PORT
from common.state.game_config import GameConfig
from common.state.player_state_diff import PlayerStateDiff
from common.tiles.tile_node_path_factory import TileNodePathFactory
from common.transfer.network_transfer import NetworkTransfer
from common.typings import Input, Messages

load_prc_file_data("", """
sync-video 0
yield-timeslice 0
client-sleep 0
multi-sleep 0
""")


class Client:
    def __init__(self, connection_manager: ConnectionManager):
        self.__game = Game()
        self.__loader = self.__game.get_loader()
        self.__game_manager = GameManager(self.__game, TileNodePathFactory(self.__loader), connection_manager)

        self.__connection_manager = connection_manager
        self.__connection_manager.on(Messages.GLOBAL_STATE, self.__game_state_change)
        self.__connection_manager.on(Messages.GAME_END, self.__game_end_handler)
        self.__connection_manager.on(Messages.BOLTS_SETUP, self.__game_manager.setup_bolts)
        self.__connection_manager.on(Messages.BOLTS_UPDATE, self.__game_manager.update_bolts)
        self.__connection_manager.on(Messages.RESUME_PLAYER, self.__game_manager.resume_player)
        self.__connection_manager.on(Messages.PLAYER_PICKED_FLAG, self.__game_manager.player_flag_pickup)
        self.__connection_manager.on(Messages.PLAYER_DROPPED_FLAG, self.__game_manager.player_flag_drop)

        self.__expected_players = 1

        # show login screen that waits for user to input username and starts the game afterward
        self.login_screen = LoginScreen(self.__loader, self.__start)
        self.waiting_screen = WaitingScreen(self.__loader)
        self.end_screen = EndScreen(self.__loader)

    def run_game(self):
        self.__game.run()

    def __start(self, username):
        self.__connection_manager.wait_for_connection(self.__ready_handler, username)
        self.__connection_manager.on(Messages.NEW_PLAYER, self.__new_player_handler)

    def __ready_handler(self, game_config: GameConfig):
        self.__expected_players = game_config.expected_players
        self.login_screen.hide()
        print(game_config.size)
        self.__game_manager.setup_map(game_config.tiles, game_config.size, game_config.season)
        for state in game_config.player_states:
            player = self.__game_manager.setup_player(state)
            if state.id == game_config.id:
                self.__game_manager.set_main_player(player)
        if self.__game_manager.get_active_players_count() < self.__expected_players:
            self.waiting_screen.display()
        else:
            self.__game.set_input_handler(self.__handle_input)
            self.__game.set_bullet_handler(self.__handle_bullet)
            self.__game_manager.set_game_has_started()

    def __game_state_change(self, game_state_transfer: NetworkTransfer):
        self.__game_manager.queue_server_game_state(game_state_transfer)

    def __new_player_handler(self, player_state: PlayerStateDiff):
        print("[INFO] New player {}".format(player_state.username))
        self.__game_manager.setup_player(player_state)
        active_players_count = self.__game_manager.get_active_players_count()
        if active_players_count >= self.__expected_players:
            if self.__game_manager.has_game_started():
                return
            self.waiting_screen.hide()
            self.__game.set_input_handler(self.__handle_input)
            self.__game.set_bullet_handler(self.__handle_bullet)
            self.__game_manager.set_game_has_started()
        else:
            self.waiting_screen.update(active_players_count, self.__expected_players)

    def __handle_bullet(self):
        direction = self.__game_manager.shoot_bullet()
        if direction is None:
            return
        timestamp = int(time.time() * 1000)
        taskMgr.do_method_later(0, lambda _: self.__connection_manager.send_gun_trigger(direction, timestamp),
                                "send input on next frame")

    def __handle_flag_drop(self):
        player_id = self.__game_manager.get_main_player_id()
        taskMgr.do_method_later(0, lambda _: self.__connection_manager.send_flag_drop_trigger(player_id),
                                "send input on next frame")

    def __handle_input(self, inp: Input):
        self.__game_manager.update_input(inp)
        # send input to server on next frame in order to give ourselves a change
        # to respond to input before server sees it
        # otherwise, we would get server response on localhost before we'd processed it locally
        taskMgr.do_method_later(0, lambda _: self.__connection_manager.send_input_update(inp),
                                "send input on next frame")

    def __game_end_handler(self, winner_id, winner_username, wins, losses):
        self.end_screen.display(self.__game_manager.get_main_player_id() == winner_id,
                                winner_username, self.__game_manager.get_main_player_username(), wins, losses)


if __name__ == "__main__":
    connection_manager = ConnectionManager((SERVER_ADDRESS, SERVER_PORT))
    client = Client(connection_manager)
    globalClock.setMode(ClockObject.MLimited)
    globalClock.setFrameRate(FRAMERATE)
    # PStatClient.connect()
    client.run_game()
