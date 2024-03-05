import random

from tilesmap import tiles_map
import PIL.Image as Image


def is_position_available(grid, x, y, players_positions):
    if tiles_map[grid[x][y].result]["available"] and (x, y) not in players_positions:
        return True
    return False


def generate_players_positions(MAP, grid, num_players):
    player = Image.open("tiles/player.png")
    players_positions = []
    rows = len(grid)
    columns = len(grid[0])
    TILE_SIZE = 62

    for _ in range(num_players):
        x = random.randint(0, columns - 1)
        y = random.randint(0, rows - 1)

        while not is_position_available(grid, x, y, players_positions):
            x = random.randint(0, columns - 1)
            y = random.randint(0, rows - 1)

        players_positions.append((x, y))
        MAP.paste(player, (y * TILE_SIZE, x * TILE_SIZE), mask=player)

    return MAP
