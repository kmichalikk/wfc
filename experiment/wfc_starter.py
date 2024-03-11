from experiment.tiles.tiles_manager import TilesManager
from experiment.wfc.wfc_generator import WFCGridGenerator
from experiment.wfc.wfc_map import WFCMap


def start_wfc(size: int, players_count: int):
    tiles_manager = TilesManager()
    generator = WFCGridGenerator(tiles_manager)
    wfc_map = WFCMap(generator, tiles_manager)
    return wfc_map.build_image_grid(size, players_count)
