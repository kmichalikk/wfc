from queue import Queue
from panda3d.core import Vec3
from common.tiles.tiles_manager import TilesManager
from server.wfc.wfc_generator import WFCGridGenerator
from server.wfc.wfc_grid import WFCGrid


class WFCMap:
    def __init__(self, generator: WFCGridGenerator, tiles_manager: TilesManager):
        self.generator = generator
        self.tiles_manager = tiles_manager

    def build_image_grid(self, size: int, players_count) -> (dict[any], [Vec3]):
        grid = self.generator.generate(size, players_count)

        result = []
        for i in range(size):
            for j in range(size):
                heading = 0
                match grid.cells[i][j].collapsed_tile[-1]:
                    case "2":
                        heading = -90
                    case "3":
                        heading = 180
                    case "4":
                        heading = 90
                result.append({"node_path": grid.cells[i][j].collapsed_tile[:-1]+"1",
                               "pos": (i*2, j*2, 0), "heading": heading})

        return result, [Vec3(pc.position[0]*2, pc.position[1]*2, 0) for pc in grid.players_cells]
