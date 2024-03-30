import simplepbr

from direct.showbase.ShowBase import ShowBase
from client.game_manager import GameManager
from client.connection.connection_manager import ConnectionManager
from common.config.game_config import GameConfig
from common.state.game_state_diff import GameStateDiff
from common.state.player_state_diff import PlayerStateDiff
from common.transfer.network_transfer import NetworkTransfer
from common.typings import Input


class Game(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)
        simplepbr.init()

        self.connection_manager = ConnectionManager(('127.0.0.1', 7654))
        self.connection_manager.wait_for_connection(self.ready_handler)
        self.connection_manager.subscribe_for_game_state_change(self.game_state_change)
        self.connection_manager.subscribe_for_new_player(self.new_player_handler)
        self.game_manager = GameManager()
        self.game_state = GameStateDiff.empty()

    def ready_handler(self, game_config: GameConfig):
        self.game_manager.setup_map(self, game_config.tiles, game_config.size)
        for state in game_config.player_states:
            self.game_manager.setup_player(self, state, game_config.id == state.id)

    def game_state_change(self, game_state_transfer: NetworkTransfer):
        self.game_manager.sync_game_state(game_state_transfer)

    def new_player_handler(self, player_state: PlayerStateDiff):
        print("[INFO] New player with id={}".format(player_state.id))
        self.game_manager.setup_player(self, player_state)

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
        self.connection_manager.send_input_update(input)


if __name__ == "__main__":
    game = Game()
    game.set_sleep(0.016)
    game.run()