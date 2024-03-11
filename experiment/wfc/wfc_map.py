from queue import Queue


from experiment.tiles.tiles_manager import TilesManager
from experiment.wfc.wfc_generator import WFCGridGenerator
from experiment.wfc.wfc_grid import WFCGrid


class WFCMap:
    def __init__(self, generator: WFCGridGenerator, tiles_manager: TilesManager):
        self.generator = generator
        self.tiles_manager = tiles_manager

    def build_image_grid(self, size: int, players_count):
        grid = self.generator.generate(size, players_count)
        graph = self.__get_graph(grid)
        players_cells_indexes = [cell.id for cell in grid.players_cells]
        while not self.__bfs_check_players_reachability(players_cells_indexes, graph):
            print("unreachable player")
            grid = self.generator.generate(size, players_count)
            graph = self.__get_graph(grid)
            players_cells_indexes = [i * size + j for i, j in [grid.players_cells]]

        result = []
        for i in range(size):
            for j in range(size):
                result.append({"node_path": grid.cells[i][j].collapsed_tile[:-1]+"1", "pos": (i*5, 0, j*5), "heading": int(grid.cells[i][j].collapsed_tile[-1])})
        return result

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
