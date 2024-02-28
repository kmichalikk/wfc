from PIL import Image
from tilesmap import tiles_map
from typing import Union
from queue import Queue, PriorityQueue
from random import randint


class WFCCell:
    def __init__(self, position: tuple[int, int], id: int):
        self.allowed_tiles: set[str] = set(tiles_map.keys())
        self.collapsed_tile: Union[str, None] = None
        self.position = position
        self.id = id

    def collapse(self) -> bool:
        choices = list(self.allowed_tiles)
        if len(choices) == 0:
            return False
        self.collapsed_tile = choices[randint(0, len(choices)-1)]
        self.allowed_tiles = {self.collapsed_tile}
        return True

    def __get_entropy(self):
        return len(self.allowed_tiles)

    def __gt__(self, other):
        e1 = self.__get_entropy()
        e2 = other.__get_entropy()
        return e1 > e2 if e1 != e2 else randint(0, 1) == 1


class WFCGrid:
    def __init__(self, size: int, cell_width: int):
        self.size = size
        self.cell_width = cell_width
        self.cells: [[WFCCell]] = [[] for _ in range(size)]
        count = 0
        for i in range(size):
            for j in range(size):
                self.cells[i].append(WFCCell((i, j), count))
                count += 1

    def generate(self):
        collapsed = [False for _ in range(self.size ** 2)]
        collapsed_count = 0
        pq: PriorityQueue[WFCCell] = PriorityQueue()
        [pq.put(cell) for cells in self.cells for cell in cells]

        while collapsed_count < self.size ** 2:
            cell = pq.get()
            if not cell.collapse():
                return False
            collapsed[cell.id] = True
            collapsed_count += 1

            pending_fix_queue: Queue[WFCCell] = Queue()
            pending_fix_queue.put(cell)
            unfinished_cell: WFCCell
            while not pending_fix_queue.empty():
                unfinished_cell = pending_fix_queue.get()
                for direction, neighbour in self.__cell_neighbours(unfinished_cell).items():
                    slots = set()
                    for allowed_tile in unfinished_cell.allowed_tiles:
                        [slots.add(tile) for tile in tiles_map[allowed_tile]["slots"][direction]]
                    new_allowed_tiles = neighbour.allowed_tiles.intersection(slots)
                    if len(new_allowed_tiles) != len(neighbour.allowed_tiles):
                        neighbour.allowed_tiles = new_allowed_tiles
                        pending_fix_queue.put(neighbour)

        return True

    def __cell_neighbours(self, cell: WFCCell) -> dict[str, WFCCell]:
        """
        Returns neighbours of cell keyed by their relative position to given cell
        (i.e. where to find the given cell starting from that neighbour)
        """
        neighbours = {}
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
                    tiles.crop(tiles_map[self.cells[i][j].collapsed_tile]["coords"]),
                    (self.cells[i][j].position[0]*self.cell_width, self.cells[i][j].position[1]*self.cell_width)
                )
        result.show()


if __name__ == "__main__":
    grid = WFCGrid(16, 64)
    while not grid.generate():
        grid = WFCGrid(16, 64)

    grid.build_image()
