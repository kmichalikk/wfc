from math import log
import numpy as np

from src.tiles.tilesmap import tiles_map
from src.typings import Direction


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
    def get_neighbours(tile_name: str, id: int, size: int) -> [int]:
        row = id // size
        neighbours = []
        for direction in tiles_map[tile_name]["neighbours"]:
            match direction:
                case "n":
                    neighbours.append(id + 1)
                case "e":
                    neighbours.append(id + size)
                case "s":
                    neighbours.append(id - 1)
                case "w":
                    neighbours.append(id - size)

        if id == (row + 1) * size - 1:
            neighbours = list(filter(lambda x: 0 <= x < size * size and x != id + 1, neighbours))
        elif id == row * size:
            neighbours = list(filter(lambda x: 0 <= x < size * size and x != id - 1, neighbours))
        else:
            neighbours = list(filter(lambda x: 0 <= x < size * size, neighbours))

        return neighbours

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
