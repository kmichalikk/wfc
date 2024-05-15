import panda3d.core as p3d

from common.config import BULLET_ENERGY
from common.objects.bullet_factory import BulletFactory
from common.transfer.network_transfer import NetworkTransfer
from common.typings import Messages
from server.chain_of_responsibility.abstract_handler import AbstractHandler
from server.typings import HandlerContext, ServerGame


class BulletHandler(AbstractHandler):
    def __init__(self, bullet_factory: BulletFactory, game: ServerGame):
        super().__init__()
        self.bullet_factory = bullet_factory
        self.game = game

    def handle(self, context: HandlerContext) -> list[NetworkTransfer]:
        if context.message != Messages.FIRE_GUN:
            return self.pass_to_next(context)

        active_players = self.game.get_active_players()
        transfer = context.get_transfer()

        if transfer.get_source() not in active_players:
            return []

        player = active_players[transfer.get_source()]
        trigger_timestamp = transfer.get("timestamp")
        if player.state.energy < BULLET_ENERGY:
            return []

        player.lose_energy(BULLET_ENERGY)
        self.shoot_bullet(
            p3d.Vec3(float(transfer.get('x')), float(transfer.get('y')), 0),
            player,
            trigger_timestamp
        )

        return []

    def shoot_bullet(self, direction, player, timestamp):
        bullet = self.bullet_factory.get_one(
            (player.get_state().get_position() + p3d.Vec3(0, 0, 0.5)
             + direction * 0.5),
            direction,
            player.get_id()
        )
        bullet.timestamp = timestamp
        self.game.add_projectile_to_process(bullet)
