from experiment.tiles.tiles_manager import TilesManager
from experiment.wfc.wfc_generator import WFCGridGenerator
from experiment.wfc.wfc_map import WFCMap

if __name__ == "__main__":
    tiles_manager = TilesManager()
    generator = WFCGridGenerator(tiles_manager)
    wfc_map = WFCMap(64, generator, tiles_manager)
    wfc_map.build_image_grid(20, 3)
