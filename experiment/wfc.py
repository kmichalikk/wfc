import random

from PIL import Image
from tilesmap import tiles_map
from typing import Union, Literal
from queue import Queue, PriorityQueue
from random import randint, shuffle
from math import log
from copy import deepcopy

type Direction = Literal["n", "e", "s", "w"]

type Corner = Literal["ul", "ur", "dl", "dr"]


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


class WFCGrid:
    def __init__(self, size, cells):
        self.size = size
        self.cells = cells
        self.players_cells: [WFCCell] = []

    def cell_neighbours(self, cell: WFCCell) -> dict[Direction, WFCCell]:
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


class WFCMap:
    def __init__(self, cell_width: int, generator: WFCGridGenerator, tiles_manager: TilesManager):
        self.generator = generator
        self.tiles_manager = tiles_manager
        self.cell_width = cell_width

    def build_image_grid(self, size: int, players_count):
        grid = self.generator.generate(size, players_count)
        graph, mapping = self.__get_graph(grid)
        players_cells_indexes = list(map(lambda c: mapping[c]["ul"], grid.players_cells))
        while not self.__bfs_check_players_reachability(players_cells_indexes, graph):
            print("unreachable player")
            grid = self.generator.generate(size, players_count)
            graph, mapping = self.__get_graph(grid)
            players_cells_indexes = list(map(lambda c: mapping[c]["ul"], grid.players_cells))

        tiles = Image.open("tiles.png")
        player = Image.open("player.png")
        result = Image.new("RGB", size=(size*self.cell_width, size*self.cell_width))
        for i in range(size):
            for j in range(size):
                position = grid.cells[i][j].position[0]*self.cell_width, grid.cells[i][j].position[1]*self.cell_width
                if grid.cells[i][j].has_player():
                    result.paste(player.resize((self.cell_width, self.cell_width)), position)
                else:
                    result.paste(
                        tiles
                        .crop(tiles_map[grid.cells[i][j].collapsed_tile]["coords"])
                        .resize((self.cell_width, self.cell_width)),
                        position
                    )
        result.show()

    def __bfs_check_players_reachability(self, players_cells_indexes, graph) -> True:
        if len(players_cells_indexes) < 2:
            return True

        queue = Queue()
        visited = [False for _ in range(len(graph))]
        queue.put(players_cells_indexes[0])
        visited[players_cells_indexes[0]] = True
        while not queue.empty():
            u = queue.get()
            for v in graph[u]:
                if visited[v]:
                    continue
                visited[v] = True
                queue.put(v)

        return all(map(lambda p: visited[p], players_cells_indexes))

    def __get_graph(self, grid: WFCGrid) -> ([[int]], dict[WFCCell, dict[Corner, int]]):
        graph = []
        nodes_count = 0
        mappings: dict[WFCCell, dict[Corner, int]] = {}
        all_cells = [c for cs in grid.cells for c in cs]
        cell: WFCCell
        for cell in all_cells:
            mappings[cell] = {}
            for corner in self.tiles_manager.get_empty_area(cell.collapsed_tile):
                mappings[cell][corner] = nodes_count
                graph.append([])
                nodes_count += 1

        for cell in all_cells:
            empty_area = self.tiles_manager.get_empty_area(cell.collapsed_tile)
            if len(empty_area) <= 1:
                continue
            for corner in empty_area:
                for other_corner in empty_area:
                    if corner == other_corner:
                        continue
                    graph[mappings[cell][corner]].append(mappings[cell][other_corner])

        for cell in all_cells:
            cell_empty_area = tiles_manager.get_empty_area(cell.collapsed_tile)
            for direction, neighbour in grid.cell_neighbours(cell).items():
                neighbour_empty_area = tiles_manager.get_empty_area(neighbour.collapsed_tile)
                if direction == "n":
                    if "dl" in neighbour_empty_area and "ul" in cell_empty_area:
                        graph[mappings[cell]["ul"]].append(mappings[neighbour]["dl"])
                    if "dr" in neighbour_empty_area and "ur" in cell_empty_area:
                        graph[mappings[cell]["ur"]].append(mappings[neighbour]["dr"])
                elif direction == "e":
                    if "ul" in neighbour_empty_area and "ur" in cell_empty_area:
                        graph[mappings[cell]["ur"]].append(mappings[neighbour]["ul"])
                    if "dl" in neighbour_empty_area and "dr" in cell_empty_area:
                        graph[mappings[cell]["dr"]].append(mappings[neighbour]["dl"])
                elif direction == "s":
                    if "ul" in neighbour_empty_area and "dl" in cell_empty_area:
                        graph[mappings[cell]["dl"]].append(mappings[neighbour]["ul"])
                    if "ur" in neighbour_empty_area and "dr" in cell_empty_area:
                        graph[mappings[cell]["dr"]].append(mappings[neighbour]["ur"])
                elif direction == "w":
                    if "ur" in neighbour_empty_area and "ul" in cell_empty_area:
                        graph[mappings[cell]["ul"]].append(mappings[neighbour]["ur"])
                    if "dr" in neighbour_empty_area and "dl" in cell_empty_area:
                        graph[mappings[cell]["dl"]].append(mappings[neighbour]["dr"])

        return graph, mappings


if __name__ == "__main__":
    tiles_manager = TilesManager()
    generator = WFCGridGenerator(tiles_manager)
    wfc_map = WFCMap(64, generator, tiles_manager)
    wfc_map.build_image_grid(20, 3)
