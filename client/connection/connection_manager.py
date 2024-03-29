from typing import Callable

from common.config.game_config import GameConfig
from common.config.player_config import PlayerConfig
from common.state.game_state_diff import GameStateDiff


class ConnectionManager:
    def wait_for_connection(self, ready_handler: Callable[[GameConfig], None]):
        pass

    def subscribe_for_game_state_change(self, subscriber: Callable[[GameStateDiff], None]):
        pass

    def subscribe_for_new_player(self, subscriber: Callable[[PlayerConfig], None]):
        pass

    def send_input_update(self, input: str):
        pass
