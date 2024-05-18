from typing import Callable
from direct.showbase.ShowBase import ShowBase
from direct.showbase.ShowBaseGlobal import aspect2d
import simplepbr

from common.objects.bolt_factory import BoltFactory
from common.objects.flag import Flag
from common.player.player_controller import PlayerController
from common.typings import Input


class Game(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)
        # proper textures & lighting
        simplepbr.init()

        aspect2d.set_transparency(True)

        self.__flag = Flag(self)
        self.__bolts_set_up = False
        self.__bolt_factory = BoltFactory(self.loader, self.render)

    def set_input_handler(self, input_handler: Callable[[Input], None]):
        self.accept("w", lambda: input_handler(Input("+forward")))
        self.accept("w-up", lambda: input_handler(Input("-forward")))
        self.accept("s", lambda: input_handler(Input("+backward")))
        self.accept("s-up", lambda: input_handler(Input("-backward")))
        self.accept("d", lambda: input_handler(Input("+right")))
        self.accept("d-up", lambda: input_handler(Input("-right")))
        self.accept("a", lambda: input_handler(Input("+left")))
        self.accept("a-up", lambda: input_handler(Input("-left")))

    def drop_flag(self, player: PlayerController):
        self.__flag.get_dropped(player)

    def get_flag_collider(self):
        return self.__flag.colliders[0]

    def pickup_flag(self, player: PlayerController):
        self.__flag.get_picked(player)

    def set_bullet_handler(self, bullet_handler: Callable[[], None]):
        self.accept("space-up", bullet_handler)

    def setup_bolts(self, current_bolts):
        if self.__bolts_set_up:
            return
        self.__bolts_set_up = True
        self.__bolt_factory.undump_bolts(current_bolts)

    def update_bolts(self, old_bolt_id, new_bolt):
        self.__bolt_factory.remove_bolt(old_bolt_id)
        self.__bolt_factory.copy_bolts([new_bolt])

    def get_loader(self):
        return self.loader
