from queue import PriorityQueue, Queue
from random import shuffle
from typing import Union

from experiment.tiles.tiles_manager import TilesManager
from experiment.wfc.wfc_cell import WFCCell
from experiment.wfc.wfc_grid import WFCGrid


class WFCGridGenerator:
    def __init__(self, tiles_manager: TilesManager):
        self.tiles_manager = tiles_manager
        self.grid: Union[WFCGrid, None] = None

    def generate(self, size: int, players_count: int) -> [[WFCCell]]:
        possible_positions = [(x, y) for x in range(size) for y in range(size)]
        shuffle(possible_positions)
        while not self.__generate(size, possible_positions[:players_count]):
            print("contradiction, trying again")
            continue

        return self.grid

    def __generate(self, size, players_positions: [tuple[int, int]]):
        size = size
        cells = [[] for _ in range(size)]
        count = 0
        for i in range(size):
            for j in range(size):
                cells[i].append(WFCCell((i, j), count, self.tiles_manager))
                count += 1

        self.grid = WFCGrid(size, cells)

        collapsed_count = len(players_positions)
        pq: PriorityQueue[WFCCell] = PriorityQueue()
        to_fix = []
        for x, y in players_positions:
            cell = cells[y][x]
            cell.set_collapsed("w")
            cell.place_player()
            self.grid.players_cells.append(cell)
            to_fix.append(cell)

        self.__fix_cells(to_fix)

        pq.put(list(filter(lambda c: not c.is_collapsed(), sorted([c for cs in cells for c in cs])))[0])

        while not pq.empty():
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
            neighbours = self.grid.cell_neighbours(unfinished_cell).items() if self.grid is not None else []
            for direction, neighbour in neighbours:
                if neighbour.is_collapsed():
                    continue
                if neighbour.update_allowed_tiles(unfinished_cell.get_slots(direction)):
                    pending_fix_queue.put(neighbour)
                    updated.add(neighbour)
        return updated
