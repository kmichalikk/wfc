from copy import deepcopy
from math import log
import numpy as np

from experiment.tiles.tilesmap import tiles_map
from experiment.typings import Direction, Corner


class TilesManager:
    def __init__(self):
        self.probabilities = {}
        weight_sum = sum([tile["weight"] for tile in tiles_map.values()])
        for key, value in tiles_map.items():
            self.probabilities[key] = value["weight"] / weight_sum

    @staticmethod
    def get_slots(tile_name: str, direction: Direction) -> set[str]:
        return {tile for tile in tiles_map[tile_name]["slots"][direction]}

    @staticmethod
    def get_empty_area(tile_name: str) -> list[Corner]:
        return deepcopy(tiles_map[tile_name]["empty_area"])

    def get_total_entropy(self, tiles: set[str]) -> float:
        entropy = 0.0
        for tile in tiles:
            entropy += -log(self.probabilities[tile]) * self.probabilities[tile]
        return entropy

    @staticmethod
    def draw_random_tile(choices: set[str]) -> str:
        tile_weights = [tiles_map[tile]["weight"] for tile in choices]
        random_index = np.random.choice(len(choices), p=(tile_weights / np.sum(tile_weights)))
        return list(choices)[random_index]
