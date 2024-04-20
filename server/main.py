import sys
import time
from collections import deque

import panda3d.core as p3d
import simplepbr
from direct.showbase.MessengerGlobal import messenger

from direct.showbase.ShowBase import ShowBase
from direct.showbase.ShowBaseGlobal import globalClock
from direct.task.TaskManagerGlobal import taskMgr
from panda3d.core import Vec3, ClockObject

from common.collision.setup import setup_collisions
from common.config import FRAMERATE, MAP_SIZE, SERVER_PORT, INV_TICK_RATE
from common.objects.bullet import Bullet
from common.objects.bullet_factory import BulletFactory
from common.player.player_controller import PlayerController
from common.state.game_config import GameConfig
from common.state.game_state_diff import GameStateDiff
from common.state.player_state_diff import PlayerStateDiff
from common.tiles.tile_node_path_factory import TileNodePathFactory
from common.connection.udp_connection_thread import UDPConnectionThread
from common.transfer.network_transfer_builder import NetworkTransferBuilder
from common.typings import Messages, Address, TimeStep
from server.wfc.wfc_starter import start_wfc

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
        self.node_path_factory = TileNodePathFactory(self.loader)
        self.network_transfer_builder = NetworkTransferBuilder()
        self.active_players: dict[Address, PlayerController] = {}
        self.game_state_history: deque[GameStateDiff] = deque()
        self.last_game_state_timestamp = 0
        self.next_player_id = 0
        self.frames_processed = 0
        self.expected_players = expected_players
        print("[INFO] Starting WFC map generation")
        self.tiles, self.player_positions = start_wfc(MAP_SIZE, 4)
        self.bullet_factory = BulletFactory(self.render)
        self.projectiles_to_process: list[Bullet] = []
        self.bullets: list[Bullet] = []
        self.__setup_collisions()
        print("[INFO] Map generated")
        if self.view:
            self.__setup_view()

    def listen(self):
        self.udp_connection.start()
        taskMgr.add(self.handle_clients, "handle client messages")
        taskMgr.add(self.handle_game_state, "broadcast global state")
        taskMgr.add(self.update_bullets, "update bullets")
        self.accept("bullet-into-wall", self.handle_bullet_hit)
        self.accept("player-damage", self.handle_player_damage)
        print(f"[INFO] Listening on port {self.port}")

    def handle_clients(self, task):
        for transfer in self.udp_connection.get_queued_transfers():
            type = transfer.get("type")
            if type == Messages.HELLO:
                print("[INFO] New client")
            elif type == Messages.FIND_ROOM:
                print("[INFO] Room requested")
                self.__find_room_for(transfer.get_source())
            elif type == Messages.UPDATE_INPUT:
                print("[INFO] Update input")
                if transfer.get_source() in self.active_players:
                    self.active_players[transfer.get_source()].update_input(transfer.get("input"))
            elif type == Messages.FIRE_GUN:
                player = self.active_players[transfer.get_source()]
                trigger_timestamp = transfer.get("timestamp")
                self.shoot_bullet(
                    p3d.Vec3(float(transfer.get('x')), float(transfer.get('y')), 0),
                    player,
                    trigger_timestamp
                )
        return task.cont

    def update_bullets(self, task):
        for bullet in self.bullets:
            bullet.update_position()
        projectiles = self.projectiles_to_process
        self.projectiles_to_process = []
        for b in projectiles:
            self.__update_position_compensate_time(b)
            self.bullets.append(b)
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
        # todo: do sth when player has been hit, only first time that event fired
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

    def __find_room_for(self, address):
        new_player_controller = self.__add_new_player(address, str(self.next_player_id))
        self.__observe_collisions(new_player_controller)
        self.network_transfer_builder.add("id", str(self.next_player_id))
        self.next_player_id += 1
        self.network_transfer_builder.set_destination(address)
        self.network_transfer_builder.add("type", Messages.FIND_ROOM_OK)
        game_config = GameConfig(
            self.tiles,
            self.expected_players,
            new_player_controller.get_id(),
            [player.get_state() for player in self.active_players.values()],
            MAP_SIZE
        )
        # fill game_config
        game_config.transfer(self.network_transfer_builder)
        # respond with data and notify other players
        self.udp_connection.enqueue_transfer(self.network_transfer_builder.encode())
        self.broadcast_new_player(
            new_player_controller.get_id(),
            new_player_controller.get_state()
        )

    def handle_game_state(self, task):
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
        address: Address
        for address in self.active_players.keys():
            # resend the same transfer to all players, change only destination
            self.network_transfer_builder.set_destination(address)
            self.udp_connection.enqueue_transfer(
                self.network_transfer_builder.encode(reset=False)
            )
        # reset=False left previous builder state, clean it up after pinging every player
        self.network_transfer_builder.cleanup()

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

    def __add_new_player(self, address: Address, id: str) -> PlayerController:
        new_player_state = PlayerStateDiff(TimeStep(begin=0, end=time.time()), id)
        new_player_state.set_position((self.player_positions[int(new_player_state.id)]))
        model = self.node_path_factory.get_player_model()
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

        return new_player_controller

    def __setup_collisions(self):
        setup_collisions(self, self.tiles, MAP_SIZE, self.bullet_factory)

    def __observe_collisions(self, player):
        self.accept('player' + player.get_id() + '-into-water', player.into_water)
        self.accept('player' + player.get_id() + '-into-grass', player.out_of_water)
        self.accept('player' + player.get_id() + '-into-safe_space0', player.into_safe_space)
        self.accept('player' + player.get_id() + '-into-safe_space1', player.into_safe_space)
        self.accept('player' + player.get_id() + '-into-safe_space2', player.into_safe_space)
        self.accept('player' + player.get_id() + '-into-safe_space3', player.into_safe_space)
        #self.accept('player' + player.get_id() + '-into-flag', player.flag_pickup, [self.flag])

    # to be called after __setup_collisions()
    def __setup_view(self):
        simplepbr.init()
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
