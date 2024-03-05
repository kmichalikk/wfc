import random
from math import log

import PIL.Image as Image

from tilesmap import tiles_map


def create_map(DIM):
    TILE_SIZE = 62
    MAP = Image.new('RGB', (DIM[0] * TILE_SIZE, DIM[1] * TILE_SIZE))

    class Tile:
        def __init__(self, x, y):
            self.x = x
            self.y = y
            self.options = list(tiles_map.keys())
            self.entropy = 100
            self.collapsed = False
            self.result = ""
            self.right = {"collapsed": None, "result": None}
            self.left = {"collapsed": None, "result": None}
            self.top = {"collapsed": None, "result": None}
            self.bottom = {"collapsed": None, "result": None}

        def draw(self):
            MAP.paste(tiles_map[self.result]["image"], (self.x * TILE_SIZE, self.y * TILE_SIZE))

        def calculate_entropy(self):
            weights_sum = 0
            logs_sum = 0
            for option in self.options:
                weights_sum += tiles_map[option]["weight"]
                logs_sum += (log(tiles_map[option]["weight"]) * tiles_map[option]["weight"])
            return log(weights_sum) - (logs_sum / weights_sum)

        def update_entropy(self, smallest_entropy):
            checked_options = []
            for option in self.options:
                valid = True
                if self.right["collapsed"] and option not in tiles_map[self.right["result"]]["slots"]["w"]:
                    valid = False
                if self.left["collapsed"] and option not in tiles_map[self.left["result"]]["slots"]["e"]:
                    valid = False
                if self.top["collapsed"] and option not in tiles_map[self.top["result"]]["slots"]["s"]:
                    valid = False
                if self.bottom["collapsed"] and option not in tiles_map[self.bottom["result"]]["slots"]["n"]:
                    valid = False

                if valid:
                    checked_options.append(option)
            self.options = checked_options
            self.entropy = self.calculate_entropy()
            if smallest_entropy is None or self.entropy < smallest_entropy:
                return self.entropy
            return smallest_entropy

        def update_neighbours(self):
            if not self.collapsed:
                if self.x < DIM[0] - 1:
                    self.right = {"collapsed": grid[self.y][self.x + 1].collapsed,
                                  "result": grid[self.y][self.x + 1].result}
                if self.y < DIM[1] - 1:
                    self.bottom = {"collapsed": grid[self.y + 1][self.x].collapsed,
                                   "result": grid[self.y + 1][self.x].result}
                if self.x > 0:
                    self.left = {"collapsed": grid[self.y][self.x - 1].collapsed,
                                 "result": grid[self.y][self.x - 1].result}
                if self.y > 0:
                    self.top = {"collapsed": grid[self.y - 1][self.x].collapsed,
                                "result": grid[self.y - 1][self.x].result}

        def collapse(self):
            try:
                if len(self.options) > 0:
                    self.collapsed = True
                    self.result = random.choice(self.options)
                    self.entropy = 0
                    self.draw()
                else:
                    raise ValueError("Error: No options available")

            except ValueError as e:
                print(f"An error occurred: {e}")

    grid = [[Tile(x, y) for x in range(DIM[0])] for y in range(DIM[1])]
    grid[0][0].collapse()

    def update():
        for row in grid:
            for tile in row:
                tile.update_neighbours()
        smallest_entropy = None
        for row in grid:
            for tile in row:
                if not tile.collapsed:
                    smallest_entropy = tile.update_entropy(smallest_entropy)
        candidates = []
        for row in grid:
            for tile in row:
                if not tile.collapsed and tile.entropy == smallest_entropy:
                    candidates.append(tile)
        if len(candidates) > 0:
            candidate = random.choice(candidates)
            candidate.collapse()

    for _ in range(DIM[0] * DIM[1]):
        update()
    return grid, MAP
