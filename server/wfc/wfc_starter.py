from common.tiles.tiles_manager import TilesManager
from server.wfc.wfc_generator import WFCGridGenerator
from server.wfc.wfc_map import WFCMap


def start_wfc(size: int, players_count: int):
    tiles_manager = TilesManager()
    generator = WFCGridGenerator(tiles_manager)
    wfc_map = WFCMap(generator, tiles_manager)
    return wfc_map.build_image_grid(size, players_count)
