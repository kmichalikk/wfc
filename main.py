from maptograph import is_map_walkable
from wfc import create_map
from playerspositions import generate_players_positions

DIM = (20, 20)
grid, MAP = create_map(DIM)
while not is_map_walkable(grid):
    grid, MAP = create_map(DIM)
MAP = generate_players_positions(MAP, grid, 5)
MAP.show()
