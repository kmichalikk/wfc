from random import randint
from typing import Union

from src.tiles.tiles_manager import TilesManager
from src.tiles.tilesmap import tiles_map
from src.typings import Direction


class WFCCell:
    def __init__(self, position: tuple[int, int], id: int, tiles_manager: TilesManager):
        self.allowed_tiles: set[str] = set(tiles_map.keys())
        self.collapsed_tile: Union[str, None] = None
        self.position = position
        self.id = id
        self.tiles_manager = tiles_manager
        self.entropy = self.tiles_manager.get_total_entropy(self.allowed_tiles)
        self.player = False

    def __repr__(self):
        return "{} ({}, {})".format(self.collapsed_tile, *self.position)

    def has_player(self):
        return self.player

    def place_player(self):
        self.player = True

    def is_collapsed(self) -> bool:
        return self.collapsed_tile is not None

    def collapse(self) -> Union[str, None]:
        choices = list(self.allowed_tiles)
        if len(choices) == 0:
            return None
        self.collapsed_tile = self.tiles_manager.draw_random_tile(self.allowed_tiles)
        self.allowed_tiles = {self.collapsed_tile}
        return self.collapsed_tile

    def set_collapsed(self, tile: str) -> Union[str, None]:
        if tile not in self.allowed_tiles:
            return None
        self.allowed_tiles = {tile}
        self.collapsed_tile = tile
        return tile

    def update_allowed_tiles(self, new_allowed_tiles: set[str]) -> bool:
        intersection = self.allowed_tiles.intersection(new_allowed_tiles)
        if len(intersection) == len(self.allowed_tiles):
            return False
        self.allowed_tiles = intersection
        self.entropy = self.tiles_manager.get_total_entropy(self.allowed_tiles)
        return True

    def get_slots(self, direction: Direction) -> set[str]:
        if self.collapsed_tile is not None:
            return self.tiles_manager.get_slots(self.collapsed_tile, direction)
        slots = set()
        for tile in self.allowed_tiles:
            for s in self.tiles_manager.get_slots(tile, direction):
                slots.add(s)
        return slots

    def get_entropy(self) -> float:
        return self.entropy

    def __gt__(self, other):
        e1 = self.get_entropy()
        e2 = self.get_entropy()
        return e1 > e2 if e1 != e2 else randint(0, 1) == 1
