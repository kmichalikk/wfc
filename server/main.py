import random
import sys
import time
from collections import deque
from typing import Union

import panda3d.core as p3d
from direct.showbase.MessengerGlobal import messenger

from direct.showbase.ShowBase import ShowBase
from direct.showbase.ShowBaseGlobal import globalClock
from direct.task.TaskManagerGlobal import taskMgr
from panda3d.core import Vec3, ClockObject

from common.collision.collision_builder import CollisionBuilder
from common.config import FRAMERATE, MAP_SIZE, SERVER_PORT, INV_TICK_RATE
from common.objects.bullet import Bullet
from common.objects.bullet_factory import BulletFactory
from common.objects.bolt_factory import BoltFactory
from common.objects.flag import Flag
from common.player.player_controller import PlayerController
from common.state.game_config import GameConfig
from common.state.game_state_diff import GameStateDiff
from common.state.player_state_diff import PlayerStateDiff
from common.tiles.tile_node_path_factory import TileNodePathFactory
from common.connection.udp_connection_thread import UDPConnectionThread
from common.transfer.network_transfer_builder import NetworkTransferBuilder
from common.typings import Messages, Address, TimeStep
from server.chain_of_responsibility.bolt_handler import BoltHandler
from server.chain_of_responsibility.bullet_handler import BulletHandler
from server.chain_of_responsibility.existing_client_handler import ExistingClientHandler
from server.chain_of_responsibility.flag_handler import FlagHandler
from server.chain_of_responsibility.freeze_player_handler import FreezePlayerHandler
from server.chain_of_responsibility.hello_handler import HelloHandler
from server.chain_of_responsibility.movement_handler import MovementHandler
from server.chain_of_responsibility.new_client_handler import NewClientHandler
from server.wfc.wfc_starter import start_wfc
from server.accounts.db_manager import DBManager
from server.typings import HandlerContext, ServerGame, SupportsServerOperationsChain

sys.path.append("../common")


class Server(ShowBase, ServerGame):
    def __init__(self, port, expected_players, view=False):
        if view:
            # show window for debug purposes, slows down everything
            super().__init__()
        else:
            super().__init__(windowType="none")
        self.view = view
        self.port = port
        self.udp_connection = UDPConnectionThread('0.0.0.0', port, server=True)
        self.db_manager = DBManager()
        self.node_path_factory = TileNodePathFactory(self.loader)
        self.network_transfer_builder = NetworkTransferBuilder()
        self.active_players: dict[Address, PlayerController] = {}
        self.game_state_history: deque[GameStateDiff] = deque()
        self.last_game_state_timestamp = 0
        self.next_player_id = 0
        self.frames_processed = 0
        self.expected_players = expected_players
        self.season = random.choices([0, 1], weights=[5, 5], k=1)[0]
        print("[INFO] Starting WFC map generation")
        self.tiles, self.player_positions = start_wfc(MAP_SIZE, 4)
        self.bullet_factory = BulletFactory(self.render)
        self.bolt_factory = BoltFactory(self.loader, self.render)
        self.bolt_factory.spawn_bolts()
        self.projectiles_to_process: list[Bullet] = []
        self.bullets: list[Bullet] = []
        self.bullets_since_last_update: list[Bullet] = []
        self.flag = Flag(self)
        self.game_won_by: Union[None, PlayerController] = None
        self.request_handlers_chain = self.__setup_chain_of_responsibility()
        self.collision_builder = CollisionBuilder(self.render, self.loader)
        self.build_collisions()
        print("[INFO] Map generated")
        if self.view:
            self.__setup_view()

    def reset_server(self):
        print("[INFO] Resetting server...")
        print("  --   Removing players")
        self.active_players = {}
        self.next_player_id = 0
        print("  --   Clearing game state history")
        self.game_state_history = deque()
        self.last_game_state_timestamp = 0
        self.frames_processed = 0
        self.flag = Flag(self)
        print("  --   Clearing scene")
        self.render.get_children().detach()
        print("  --   Generating new map")
        self.season = random.choices([0, 1], weights=[5, 5], k=1)[0]
        self.tiles, self.player_positions = start_wfc(MAP_SIZE, 4)
        self.request_handlers_chain = self.__setup_chain_of_responsibility()
        print("  --   Starting")
        self.build_collisions()
        self.game_won_by = None
        if self.view:
            self.camera.reparent_to(self.render)
            self.__setup_view()
        print("  --   Done. Server ready")

    def listen(self):
        self.udp_connection.start()
        taskMgr.add(self.__handle_clients, "handle client messages")
        taskMgr.add(self.handle_game_state, "broadcast global state")
        taskMgr.add(self.__update_bullets, "update bullets")
        self.accept("bullet-into-wall", self.__handle_bullet_hit)
        self.accept("player-damage", self.__handle_player_damage)
        print(f"[INFO] Listening on port {self.port}")

    def get_active_players(self) -> dict[Address, PlayerController]:
        return self.active_players

    def add_projectile_to_process(self, bullet: Bullet):
        self.projectiles_to_process.append(bullet)

    def get_game_config(self, player_id: str) -> GameConfig:
        return GameConfig(
            self.tiles,
            self.expected_players,
            player_id,
            [player.get_state() for player in self.active_players.values()],
            MAP_SIZE,
            self.season
        )

    def __handle_clients(self, task):
        if self.game_won_by is not None:
            return

        known_addresses = list(self.active_players.keys())
        for transfer in self.udp_connection.get_queued_transfers():
            message = Messages(int(transfer.get("type")))
            response_transfers = self.request_handlers_chain.handle(
                HandlerContext(message, transfer, known_addresses)
            )
            for response_transfer in response_transfers:
                self.udp_connection.enqueue_transfer(response_transfer)
        return task.cont

    def __setup_chain_of_responsibility(self) -> SupportsServerOperationsChain:
        handlers: list[SupportsServerOperationsChain]
        handlers = [
            HelloHandler(),
            NewClientHandler(self, self.__add_new_player, self.flag, self.bolt_factory, self.db_manager),
            ExistingClientHandler(self),
            FreezePlayerHandler(self.freeze_player),
            BulletHandler(self.bullet_factory, self),
            BoltHandler(self.bolt_factory),
            FlagHandler(self.flag, self),
            MovementHandler(self)
        ]

        for i in range(1, len(handlers)):
            handlers[i].set_next(handlers[i - 1])

        return handlers[-1]

    def build_collisions(self):
        self.collision_builder.add_colliders_from(self.flag)
        for bullet in self.bullet_factory.bullets:
            self.collision_builder.add_colliders_from(bullet)
        self.collision_builder.add_tile_colliders(self.tiles, self.season)
        self.collision_builder.add_safe_spaces(MAP_SIZE)
        self.cTrav = self.collision_builder.get_collision_system()

    def __update_bullets(self, task):
        if self.game_won_by is not None:
            return

        for bullet in self.bullets:
            bullet.update_position()
        projectiles = self.projectiles_to_process
        self.projectiles_to_process = []
        for b in projectiles:
            self.__update_position_compensate_time(b)
            self.bullets.append(b)
            self.bullets_since_last_update.append(b)
        return task.cont

    def __handle_bullet_hit(self, entry):
        if "wall" in entry.get_into_node_path().get_name():
            bullet_id = entry.get_from_node_path().get_tag('id')
            self.bullets = [b for b in self.bullets if b.bullet_id != bullet_id]
            self.bullet_factory.destroy(int(bullet_id))
        else:
            messenger.send("player-damage", [entry.get_into_node_path().get_tag('id')])

    def __handle_player_damage(self, data):
        player_id = data[0]
        self.handle_flag_drop(self.get_address_by_id(player_id), player_id)
        print("player {} was hit".format(player_id))

    def __update_position_compensate_time(self, projectile: Bullet):
        timestamp_sec = projectile.timestamp / 1000
        last_history_index = len(self.game_state_history) - 1  # should NOT be empty
        i = last_history_index
        while i > 0 and self.game_state_history[i].step.begin > timestamp_sec:
            i -= 1
        players_to_skip = [projectile.owner_id]

        def check_hit(states, projectile_position):
            nonlocal players_to_skip
            state: PlayerStateDiff
            for state in states:
                if state.id in players_to_skip:
                    continue
                length = (state.get_position() - projectile_position + p3d.Vec3(0, 0, 0.5)).length()
                if length < PlayerController.COLLISION_RADIUS:
                    players_to_skip.append(state.id)
                    messenger.send("player-damage", [state.id])
                    print("compensated for player {} hit".format(state.id))

        check_hit(self.game_state_history[i].player_state.values(), projectile.position)

        samples = 5
        while i <= last_history_index:
            dt = (self.game_state_history[i].step.end - timestamp_sec) / samples
            for _ in range(samples):  # for more precision in finding hits
                projectile.update_position_by_dt(dt)
                check_hit(self.game_state_history[i].player_state.values(), projectile.position)
            timestamp_sec = self.game_state_history[i].step.end
            i += 1
        pass

    def handle_game_state(self, task):
        if self.game_won_by is not None:
            return

        # prepare current snapshot of game state
        game_state = GameStateDiff(TimeStep(begin=0, end=time.time()))
        game_state.player_state \
            = {player.get_id(): player.get_state() for player in self.active_players.values()}
        # broadcast states "tick rate" times per second
        self.frames_processed += 1
        if self.frames_processed % INV_TICK_RATE == 0:  # i.e. 60fps / 3 = tick rate 20
            self.__broadcast_game_state(game_state)

        # save the snapshot to history
        game_state.step = TimeStep(begin=self.last_game_state_timestamp, end=game_state.step.end)
        self.game_state_history.append(game_state)
        while len(self.game_state_history) > 0 \
                and self.game_state_history[0].step.end < time.time() - 0.5:
            self.game_state_history.popleft()

        return task.cont

    def __broadcast_game_state(self, game_state):
        self.network_transfer_builder.add("type", Messages.GLOBAL_STATE)
        game_state.transfer(self.network_transfer_builder)

        all_bullets = self.bullets_since_last_update
        self.bullets_since_last_update = []

        address: Address

        for address in self.active_players.keys():
            self.network_transfer_builder.add(
                "bullets",
                self.__get_other_players_bullets_metadata(all_bullets, self.active_players[address].get_id())
            )
            self.network_transfer_builder.set_destination(address)
            self.udp_connection.enqueue_transfer(
                self.network_transfer_builder.encode(reset=False)
            )
        # reset=False left previous builder state, clean it up after pinging every player
        self.network_transfer_builder.cleanup()

    def __get_other_players_bullets_metadata(self, all_bullets: list[Bullet], player_id: str):
        bullets = [b for b in all_bullets if b.owner_id != player_id]
        new_bullets_metadata = ""
        for b in bullets:
            new_bullets_metadata += f"{' '.join([str(md) for md in b.get_metadata()])},"
        return new_bullets_metadata[:-1]

    def __add_new_player(self, address: Address, username: str) -> str:
        new_player_id = self.next_player_id
        self.next_player_id += 1
        new_player_state = PlayerStateDiff(TimeStep(begin=0, end=time.time()), str(new_player_id), username)
        new_player_state.set_position((self.player_positions[int(new_player_state.id)]))
        model = self.node_path_factory.get_player_model(new_player_state.id)
        model.reparent_to(self.render)
        new_player_controller = PlayerController(model, new_player_state)
        self.active_players[address] = new_player_controller
        new_player_controller.sync_position()

        self.collision_builder.add_colliders_from(new_player_controller, self.view)

        taskMgr.add(new_player_controller.task_update_position, "update player position")
        self.accept(f"bullet-into-player{new_player_id}", self.__handle_bullet_hit)
        self.accept(
            f"player{new_player_id}-into-safe_space{new_player_id}",
            self.__add_player_into_safe_space_handler(new_player_controller)
        )

        return new_player_controller.get_id()

    def __setup_view(self):
        self.disableMouse()

        properties = p3d.WindowProperties()
        properties.set_size(1280, 800)
        self.win.request_properties(properties)

        point_light_node = self.render.attach_new_node(p3d.PointLight("light"))
        point_light_node.set_pos(0, -10, 10)
        self.render.set_light(point_light_node)
        self.camera.set_pos(Vec3(MAP_SIZE, MAP_SIZE, 5 * MAP_SIZE))
        self.camera.look_at(Vec3(MAP_SIZE, MAP_SIZE, 0))
        for c in self.collision_builder.get_tile_colliders():
            c.show()

    def get_address_by_id(self, player_id):
        for address, player_controller in self.active_players.items():
            if player_controller.get_id() == player_id:
                return address
        return None

    def __add_player_into_safe_space_handler(self, player_controller: PlayerController):
        def handler(entry):
            if player_controller.has_flag():
                print(f"[INFO] player{player_controller.get_id()} has won the game")
                self.game_won_by = player_controller
                self.__finish_game()

        return handler

    def __finish_game(self):
        for i in range(5):
            print(f"[INFO] Broadcasting game end {i + 1}th time")
            self.network_transfer_builder.add("type", Messages.GAME_END)
            self.network_transfer_builder.add("id", self.game_won_by.get_id())
            self.network_transfer_builder.add("username", self.game_won_by.get_username())

            address: Address
            for address in self.active_players.keys():
                # resend the same transfer to all players, change only destination
                username = self.active_players[address].get_username()
                if username == self.game_won_by.get_username():
                    self.db_manager.update_wins(username)
                else:
                    self.db_manager.update_losses(username)

                wins, losses = self.db_manager.get_user_stats(username)
                self.network_transfer_builder.add("wins", wins)
                self.network_transfer_builder.add("losses", losses)

                self.network_transfer_builder.set_destination(address)
                self.udp_connection.enqueue_transfer(
                    self.network_transfer_builder.encode(reset=False)
                )
            # reset=False left previous builder state, clean it up after pinging every player
            self.network_transfer_builder.cleanup()
        time.sleep(0.5)
        self.reset_server()

    def freeze_player(self, address: Address):
        if address in self.active_players.keys():
            player = self.active_players[address]
            player.freeze()
            self.handle_flag_drop(address, player.get_id())
            taskMgr.do_method_later(4, lambda _: self.resume_player(address, player), "enable movement")

    def handle_flag_drop(self, player_address, player):
        if self.flag.taken() and player == self.flag.player.get_id():
            print("[INFO] Flag dropped by player " + player)
            addresses = self.active_players.keys()
            for address in addresses:
                self.network_transfer_builder.set_destination(address)
                self.network_transfer_builder.add("type", Messages.PLAYER_DROPPED_FLAG)
                self.network_transfer_builder.add("player", player)

                self.udp_connection.enqueue_transfer(self.network_transfer_builder.encode())
            self.player_flag_drop(player_address)

    def player_flag_drop(self, address):
        player = self.active_players[address]
        self.flag.get_dropped(player)

    def resume_player(self, address, player):
        player.resume()
        self.network_transfer_builder.set_destination(address)
        self.network_transfer_builder.add("type", Messages.RESUME_PLAYER)
        self.udp_connection.enqueue_transfer(self.network_transfer_builder.encode())


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Użycie: python -m server.main <liczba graczy>")
        sys.exit(1)
    expected_players = int(sys.argv[1])
    # server = Server(SERVER_PORT, 1, True)  # this slows down the whole simulation, debug only
    server = Server(SERVER_PORT, expected_players)
    globalClock.setMode(ClockObject.MLimited)
    globalClock.setFrameRate(FRAMERATE)
    server.listen()
    print(f"[INFO] Starting game loop")
    server.run()
