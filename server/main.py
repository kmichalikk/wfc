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

from common.collision.setup import setup_collisions
from common.config import FRAMERATE, MAP_SIZE, SERVER_PORT, INV_TICK_RATE, BULLET_ENERGY
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
from server.wfc.wfc_starter import start_wfc
from server.accounts.db_manager import DBManager

sys.path.append("../common")


class Server(ShowBase):
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
        self.__setup_collisions()
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
        print("  --   Starting")
        self.__setup_collisions()
        self.game_won_by = None
        if self.view:
            self.camera.reparent_to(self.render)
            self.__setup_view()
        print("  --   Done. Server ready")

    def listen(self):
        self.udp_connection.start()
        taskMgr.add(self.handle_clients, "handle client messages")
        taskMgr.add(self.handle_game_state, "broadcast global state")
        taskMgr.add(self.update_bullets, "update bullets")
        self.accept("bullet-into-wall", self.handle_bullet_hit)
        self.accept("player-damage", self.handle_player_damage)
        print(f"[INFO] Listening on port {self.port}")

    def handle_clients(self, task):
        if self.game_won_by is not None:
            return

        for transfer in self.udp_connection.get_queued_transfers():
            type = transfer.get("type")
            if type == Messages.HELLO:
                print("[INFO] New client")
            elif type == Messages.FIND_ROOM:
                print("[INFO] Room requested")
                self.__find_room_for(transfer.get_source(), transfer.get("username"))
            elif type == Messages.UPDATE_INPUT:
                if transfer.get_source() in self.active_players:
                    print("[INFO] Update input")
                    self.active_players[transfer.get_source()].update_input(transfer.get("input"))
            elif type == Messages.FIRE_GUN:
                if transfer.get_source() in self.active_players:
                    player = self.active_players[transfer.get_source()]
                    trigger_timestamp = transfer.get("timestamp")
                    if player.state.energy < BULLET_ENERGY:
                        return
                    player.lose_energy(BULLET_ENERGY)
                    self.shoot_bullet(
                        p3d.Vec3(float(transfer.get('x')), float(transfer.get('y')), 0),
                        player,
                        trigger_timestamp
                    )
            elif type == Messages.FLAG_PICKED:
                print("[INFO] Flag requested by player " + transfer.get("player"))
                self.handle_flag_pickup(transfer.get_source(), transfer.get("player"))
            elif type == Messages.FLAG_DROPPED:
                print("[INFO] Flag drop requested by player " + transfer.get("player"))
                self.handle_flag_drop(transfer.get_source(), transfer.get("player"))
            elif type == Messages.PLAYER_PICKED_BOLT:
                self.update_bolts(transfer.get("bolt_id"))
            elif type == Messages.FREEZE_PLAYER:
                self.freeze_player(transfer.get("player"))
        return task.cont

    def update_bullets(self, task):
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

    def shoot_bullet(self, direction, player, timestamp) -> p3d.Vec3:
        bullet = self.bullet_factory.get_one(
            (player.get_state().get_position() + p3d.Vec3(0, 0, 0.5)
             + direction * 0.5),
            direction,
            player.get_id()
        )
        bullet.timestamp = timestamp
        self.projectiles_to_process.append(bullet)

    def handle_bullet_hit(self, entry):
        if "wall" in entry.get_into_node_path().get_name():
            bullet_id = entry.get_from_node_path().get_tag('id')
            self.bullets = [b for b in self.bullets if b.bullet_id != bullet_id]
            self.bullet_factory.destroy(int(bullet_id))
        else:
            messenger.send("player-damage", [entry.get_into_node_path().get_tag('id')])

    def handle_player_damage(self, data):
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

    def __find_room_for(self, address, username):
        if len(self.active_players) >= 4:
            self.network_transfer_builder.set_destination(address)
            self.network_transfer_builder.add("type", Messages.FIND_ROOM_FAIL)
            self.udp_connection.enqueue_transfer(self.network_transfer_builder.encode())
            return

        new_player = True
        if address in self.active_players.keys():
            new_player = False
            player_controller = self.active_players[address]
            print(f"  --   Resending to player {player_controller.get_id()}")
            self.network_transfer_builder.add("id", player_controller.get_id())
        else:
            print("  --   Adding new player")
            player_controller = self.__add_new_player(address, str(self.next_player_id), username)
            self.network_transfer_builder.add("id", str(self.next_player_id))
            self.next_player_id += 1
        self.network_transfer_builder.set_destination(address)
        self.network_transfer_builder.add("type", Messages.FIND_ROOM_OK)
        game_config = GameConfig(
            self.tiles,
            self.expected_players,
            player_controller.get_id(),
            [player.get_state() for player in self.active_players.values()],
            MAP_SIZE,
            self.season
        )
        # fill game_config
        game_config.transfer(self.network_transfer_builder)
        self.udp_connection.enqueue_transfer(self.network_transfer_builder.encode())

        if not new_player:
            return

        # respond with data and notify other players
        self.broadcast_new_player(
            player_controller.get_id(),
            player_controller.get_state()
        )
        self.update_flag_state(address)
        self.log_in(username)
        self.setup_bolts(address)

    def handle_flag_pickup(self, player_address, player):
        if not self.flag.taken():
            print("[INFO] Flag picked by player " + player)
            addresses = self.active_players.keys()
            for address in addresses:
                self.network_transfer_builder.set_destination(address)
                self.network_transfer_builder.add("type", Messages.PLAYER_PICKED_FLAG)
                self.network_transfer_builder.add("player", player)

                self.udp_connection.enqueue_transfer(self.network_transfer_builder.encode())
            self.player_flag_pickup(player_address)

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

    def broadcast_player_disconnected(self, task):
        # todo: client is active as long as it sends KEEP_ALIVE from time to time
        #       if it haven't send anything for a minute, then remove it and notify others
        pass

    def broadcast_new_player(self, player_id, state):
        print("[INFO] Notifying players about new player")
        self.network_transfer_builder.add("type", Messages.NEW_PLAYER)
        self.network_transfer_builder.add("id", player_id)
        state.transfer(self.network_transfer_builder)
        for address, player in self.active_players.items():
            if player.get_id() == player_id:
                continue
            self.network_transfer_builder.set_destination(address)
            self.udp_connection.enqueue_transfer(
                self.network_transfer_builder.encode(reset=False)
            )
        # reset=False left previous builder state, clean it up after pinging every player
        self.network_transfer_builder.cleanup()

    def __add_new_player(self, address: Address, id: str, username: str) -> PlayerController:
        new_player_state = PlayerStateDiff(TimeStep(begin=0, end=time.time()), id, username)
        new_player_state.set_position((self.player_positions[int(new_player_state.id)]))
        model = self.node_path_factory.get_player_model(new_player_state.id)
        model.reparent_to(self.render)
        new_player_controller = PlayerController(model, new_player_state)
        self.active_players[address] = new_player_controller
        new_player_controller.sync_position()

        player_collider = new_player_controller.colliders[0]
        self.cTrav.addCollider(player_collider, self.pusher)
        self.pusher.addCollider(player_collider, player_collider)
        if self.view:
            player_collider.show()

        taskMgr.add(new_player_controller.task_update_position, "update player position")
        self.accept(f"bullet-into-player{id}", self.handle_bullet_hit)
        self.accept(
            f"player{id}-into-safe_space{id}",
            self.__add_player_into_safe_space_handler(new_player_controller)
        )

        return new_player_controller

    def log_in(self, username):
        self.db_manager.login(username)

    def __setup_collisions(self):
        setup_collisions(self, self.tiles, MAP_SIZE, self.bullet_factory)

    # to be called after __setup_collisions()
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
        for c in self.tile_colliders:
            c.show()

    def player_flag_pickup(self, address):
        player = self.active_players[address]
        self.flag.get_picked(player)

    def player_flag_drop(self, address):
        player = self.active_players[address]
        self.flag.get_dropped(player)

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
            print(f"[INFO] Broadcasting game end {i+1}th time")
            self.network_transfer_builder.add("type", Messages.GAME_END)
            self.network_transfer_builder.add("id", self.game_won_by.get_id())
            self.network_transfer_builder.add("username", self.game_won_by.get_username())

            address: Address
            for address in self.active_players.keys():
                # resend the same transfer to all players, change only destination
                self.network_transfer_builder.set_destination(address)
                self.udp_connection.enqueue_transfer(
                    self.network_transfer_builder.encode(reset=False)
                )
            # reset=False left previous builder state, clean it up after pinging every player
            self.network_transfer_builder.cleanup()
        time.sleep(0.5)
        self.reset_server()

    def update_flag_state(self, address):
        if self.flag.taken():
            self.network_transfer_builder.set_destination(address)
            self.network_transfer_builder.add("type", Messages.PLAYER_PICKED_FLAG)
            self.network_transfer_builder.add("player", self.flag.player.get_id())

            self.udp_connection.enqueue_transfer(self.network_transfer_builder.encode())

    def update_bolts(self, bolt_id):
        self.bolt_factory.remove_bolt(bolt_id)
        new_bolt = self.bolt_factory.add_bolt()

        for address, player_controller in self.active_players.items():
            self.network_transfer_builder.set_destination(address)
            self.network_transfer_builder.add("type", Messages.BOLTS_UPDATE)
            self.network_transfer_builder.add("old_bolt", bolt_id)
            self.network_transfer_builder.add("new_bolt", new_bolt)
            self.udp_connection.enqueue_transfer(self.network_transfer_builder.encode())

    def setup_bolts(self, address):
        self.network_transfer_builder.set_destination(address)
        self.network_transfer_builder.add("type", Messages.BOLTS_SETUP)
        self.network_transfer_builder.add("current_bolts", self.bolt_factory.current_bolts)
        self.udp_connection.enqueue_transfer(self.network_transfer_builder.encode())

    def freeze_player(self, player_id):
        address = self.get_address_by_id(player_id)
        if address in self.active_players.keys():
            player = self.active_players[address]
            player.freeze()
            self.handle_flag_drop(address, player_id)
            taskMgr.do_method_later(4, lambda _: self.resume_player(address, player), "enable movement")

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
    #server = Server(SERVER_PORT, 1, True)  # this slows down the whole simulation, debug only
    server = Server(SERVER_PORT, expected_players)
    globalClock.setMode(ClockObject.MLimited)
    globalClock.setFrameRate(FRAMERATE)
    server.listen()
    print(f"[INFO] Starting game loop")
    server.run()
