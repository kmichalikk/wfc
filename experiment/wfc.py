from PIL import Image
from tilesmap import tiles_map
from typing import Union, Literal
from queue import Queue, PriorityQueue
from random import randint
from math import log

type Direction = Literal["n", "e", "s", "w"]


def mirror_direction(direction: Direction) -> Direction:
    match direction:
        case "n": return "s"
        case "s": return "n"
        case "e": return "w"
        case "w": return "e"


class TilesManager:
    def __init__(self):
        self.probabilities = {}
        weight_sum = sum([tile["weight"] for tile in tiles_map.values()])
        for key, value in tiles_map.items():
            self.probabilities[key] = value["weight"] / weight_sum

    @staticmethod
    def get_slots(tile_name: str, direction: Direction) -> set[str]:
        return {tile for tile in tiles_map[tile_name]["slots"][direction]}

    def get_total_entropy(self, tiles: set[str]) -> float:
        entropy = 0.0
        for tile in tiles:
            entropy += -log(self.probabilities[tile]) * self.probabilities[tile]
        return entropy

    @staticmethod
    def draw_random_tile(choices: set[str]) -> str:
        list = []
        for tile in choices:
            for _ in range(tiles_map[tile]["weight"]):
                list.append(tile)
        return list[randint(0, len(list)-1)]


class WFCCell:
    def __init__(self, position: tuple[int, int], id: int, tiles_manager: TilesManager):
        self.allowed_tiles: set[str] = set(tiles_map.keys())
        self.collapsed_tile: Union[str, None] = None
        self.position = position
        self.id = id
        self.tiles_manager = tiles_manager
        self.entropy = self.tiles_manager.get_total_entropy(self.allowed_tiles)

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


class WFCGrid:
    def __init__(self, size: int, cell_width: int):
        self.size = size
        self.cell_width = cell_width
        self.cells: [[WFCCell]] = [[] for _ in range(size)]
        self.tiles_manager = TilesManager()
        count = 0
        for i in range(size):
            for j in range(size):
                self.cells[i].append(WFCCell((i, j), count, self.tiles_manager))
                count += 1

    def generate(self):
        collapsed_count = 0
        pq: PriorityQueue[WFCCell] = PriorityQueue()
        pq.put(self.cells[randint(0, self.size-1)][randint(0, self.size-1)])

        while collapsed_count < self.size ** 2:
            cell = pq.get()
            if cell.is_collapsed():
                continue

            collapsed_tile = cell.collapse()
            if collapsed_tile is None:
                return False

            collapsed_count += 1

            updated = self.__fix_cells([cell])
            for tile in updated:
                pq.put(tile)

        return True

    def __fix_cells(self, cells: [WFCCell]) -> [WFCCell]:
        pending_fix_queue: Queue[WFCCell] = Queue()
        updated: [WFCCell] = set()
        for cell in cells:
            pending_fix_queue.put(cell)
        unfinished_cell: WFCCell
        while not pending_fix_queue.empty():
            unfinished_cell = pending_fix_queue.get()
            for direction, neighbour in self.__cell_neighbours(unfinished_cell).items():
                if neighbour.is_collapsed():
                    continue
                if neighbour.update_allowed_tiles(unfinished_cell.get_slots(direction)):
                    pending_fix_queue.put(neighbour)
                    updated.add(neighbour)
        return updated

    def __cell_neighbours(self, cell: WFCCell) -> dict[Direction, WFCCell]:
        """
        Returns neighbours of cell keyed by their relative position to given cell
        (i.e. where to find the given cell starting from that neighbour)
        """
        neighbours: dict[Direction, WFCCell] = {}
        if cell.position[1] > 0:
            neighbours["n"] = self.cells[cell.position[0]][cell.position[1]-1]
        if cell.position[0] < self.size-1:
            neighbours["e"] = self.cells[cell.position[0]+1][cell.position[1]]
        if cell.position[1] < self.size-1:
            neighbours["s"] = self.cells[cell.position[0]][cell.position[1]+1]
        if cell.position[0] > 0:
            neighbours["w"] = self.cells[cell.position[0]-1][cell.position[1]]

        return neighbours

    def build_image(self):
        tiles = Image.open("tiles.png")
        result = Image.new("RGB", size=(self.size*self.cell_width, self.size*self.cell_width))
        for i in range(self.size):
            for j in range(self.size):
                result.paste(
                    tiles
                    .crop(tiles_map[self.cells[i][j].collapsed_tile]["coords"])
                    .resize((self.cell_width, self.cell_width)),
                    (self.cells[i][j].position[0]*self.cell_width, self.cells[i][j].position[1]*self.cell_width)
                )
        result.show()


if __name__ == "__main__":
    size = 40
    grid = WFCGrid(size, 32)
    while not grid.generate():
        print("miss!")
        grid = WFCGrid(size, 32)

    grid.build_image()
