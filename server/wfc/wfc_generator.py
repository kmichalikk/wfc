import random

from queue import PriorityQueue, Queue
from typing import Union

from common.tiles.tiles_manager import TilesManager
from server.wfc.wfc_cell import WFCCell
from server.wfc.wfc_grid import WFCGrid


class WFCGridGenerator:
    def __init__(self, tiles_manager: TilesManager):
        self.tiles_manager = tiles_manager
        self.grid: Union[WFCGrid, None] = None

    def generate(self, size: int, players_count: int) -> [[WFCCell]]:
        possible_positions = [(2, 2), (2, size - 3), (size - 3, 2), (size - 3, size - 3)]
        while not self.__generate(size, possible_positions[:players_count]):
            print("  --   [WFC] contradiction, trying again")
            continue

        return self.grid

    def __generate(self, size, players_positions: [tuple[int, int]]):
        cells = [[] for _ in range(size)]
        count = 0
        for x in range(size):
            for y in range(size):
                cells[x].append(WFCCell((x, y), count, self.tiles_manager))
                count += 1

        self.grid = WFCGrid(size, cells)

        pq: PriorityQueue[WFCCell] = PriorityQueue()
        to_fix = []
        cell = cells[4][4]
        cell.set_collapsed("empty_1")
        to_fix.append(cell)

        # add borders
        for x in range(0, size):
            cells[x][0].set_collapsed("full_1")
            cells[0][x].set_collapsed("full_1")
            cells[size-1][x].set_collapsed("full_1")
            cells[x][size-1].set_collapsed("full_1")
            to_fix.extend([cells[x][0], cells[0][x], cells[size-1][x], cells[x][size-1]])

        # make sure players can reach each other
        for i in range(2, size - 2):
            for j in range(3, size - 3):
                if i == j or i + j == size - 1:
                    cell = cells[i][j]
                    cell.set_collapsed(random.choices(["empty_1", "plants_1"], weights=[8, 2], k=1)[0])
                    to_fix.append(cell)

        # sprinkle some empty spaces
        for i, j in [(random.randint(2, size-3), random.randint(2, size-3)) for _ in range(10)]:
            cell = cells[i][j]
            cell.set_collapsed(random.choices(["empty_1", "plants_1"], weights=[8, 2], k=1)[0])
            to_fix.append(cell)

        for x, y in players_positions:
            cell = cells[x][y]
            cell.set_collapsed("empty_1")
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

            updated = self.__fix_cells([cell])
            for tile in updated:
                pq.put(tile)

        for row in cells:
            for cell in row:
                if not cell.is_collapsed():
                    return False

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
