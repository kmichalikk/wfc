from queue import Queue

from PIL import Image

from experiment.tiles.tiles_manager import TilesManager
from experiment.tiles.tilesmap import tiles_map
from experiment.typings import Corner
from experiment.wfc.wfc_cell import WFCCell
from experiment.wfc.wfc_generator import WFCGridGenerator
from experiment.wfc.wfc_grid import WFCGrid


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

    @staticmethod
    def __bfs_check_players_reachability(players_cells_indexes, graph) -> True:
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
            cell_empty_area = self.tiles_manager.get_empty_area(cell.collapsed_tile)
            for direction, neighbour in grid.cell_neighbours(cell).items():
                neighbour_empty_area = self.tiles_manager.get_empty_area(neighbour.collapsed_tile)
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
