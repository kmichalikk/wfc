import random
from common.config import MAP_SIZE

from common.objects.bolt import Bolt
from collections import deque
from panda3d.core import Vec3


class BoltFactory:
    def __init__(self, loader, render):
        self.loader = loader
        self.render = render
        self.current_bolts = []
        self.ids_set = {str(i) for i in range(0, MAP_SIZE//2)}
        self.possible_positions = deque()

        for i in range(6, 2 * MAP_SIZE - 5):
            for j in range(6, 2 * MAP_SIZE - 5):
                self.possible_positions.append(Vec3(i, j, 0))

        random.shuffle(self.possible_positions)

    def spawn_bolts(self):
        while len(self.current_bolts) < MAP_SIZE//2:
            self.add_bolt()

    def remove_bolt(self, bolt_id):
        for bolt in self.current_bolts:
            if bolt.id == bolt_id:
                self.possible_positions.appendleft(bolt.position)
                self.ids_set.add(bolt.id)
                self.current_bolts.remove(bolt)
                bolt.remove()

    def add_bolt(self):
        new_position = self.possible_positions.pop()
        new_bolt = Bolt(self.loader, self.render, new_position, self.ids_set.pop())
        self.current_bolts.append(new_bolt)
        return new_bolt

    def copy_bolts(self, bolts):
        for bolt in bolts:
            self.current_bolts.append(Bolt(self.loader, self.render, bolt.position, bolt.id))
