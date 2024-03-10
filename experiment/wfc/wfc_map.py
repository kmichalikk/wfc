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
        graph = self.__get_graph(grid)
        players_cells_indexes = [cell.id for cell in grid.players_cells]
        while not self.__bfs_check_players_reachability(players_cells_indexes, graph):
            print("unreachable player")
            grid = self.generator.generate(size, players_count)
            graph = self.__get_graph(grid)
            players_cells_indexes = [i * size + j for i, j in [grid.players_cells]]

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

    def __get_graph(self, grid: WFCGrid) -> [[int]]:
        graph = [[] for _ in range(grid.size * grid.size)]
        for j in range(grid.size):
            for i in range(grid.size):
                id = grid.cells[i][j].id
                graph[id].extend(self.tiles_manager.get_neighbours(grid.cells[i][j].collapsed_tile, id, grid.size))
        return graph
