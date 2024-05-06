import random
from common.config import MAP_SIZE

from common.objects.bolt import Bolt
from collections import deque
import panda3d.core as p3d


class BoltFactory:
    def __init__(self, loader, render):
        self.loader = loader
        self.render = render
        self.current_bolts = []
        self.ids_set = {str(i) for i in range(0, MAP_SIZE//2)}
        self.possible_positions = deque()

        for i in range(6, 2 * MAP_SIZE - 5):
            for j in range(6, 2 * MAP_SIZE - 5):
                self.possible_positions.append(p3d.Vec3(i, j, 0))

        random.shuffle(self.possible_positions)

    def dump_bolts(self):
        dump = ""
        b: Bolt
        for b in self.current_bolts:
            dump += f"{b.id} {b.position.get_x()} {b.position.get_y()},"
        return dump[:-1]

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

    def undump_bolts(self, dump):
        if dump == "":
            return
        raw_data = dump.split(",")
        for data in raw_data:
            bullet_data = data.split(" ")
            self.current_bolts.append(
                Bolt(
                    self.loader,
                    self.render,
                    p3d.Vec3(float(bullet_data[1]), float(bullet_data[2]), 0),
                    bullet_data[0]
                )
            )
