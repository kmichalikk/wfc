import csv

tiles_map = {}
with open('slots.csv', 'r') as file:
    reader = csv.reader(file)
    first_row = next(reader)
    for tile in first_row:
        if len(tile) > 1:
            tiles_map[tile.lstrip()[:-2]] = {
                "weight": 0,
                "slots": {
                    "n": set(),
                    "e": set(),
                    "s": set(),
                    "w": set()
                },
                "neighbours": []
            }
    for row in reader:
        for i in range(1, len(row)):
            tiles_map[row[0].lstrip()[:-2]]["slots"][row[0][-1]].add(first_row[i].lstrip()[:-2])

    for tile in tiles_map:
        if "empty" in tile:
            tiles_map[tile]["weight"] = 20
        elif "water_full" in tile:
            tiles_map[tile]["weight"] = 1
        elif "water" in tile:
            tiles_map[tile]["weight"] = 3
        else:
            tiles_map[tile]["weight"] = 5

        match tile:
            case "empty_1":
                tiles_map[tile]["neighbours"].extend(["n", "e", "s", "w"])
            case "plants_1":
                tiles_map[tile]["neighbours"].extend(["n", "e", "s", "w"])
            case "wall_concave_1":
                tiles_map[tile]["neighbours"].extend(["n", "e", "s", "w"])
            case "wall_convex_1":
                tiles_map[tile]["neighbours"].extend(["e", "s"])
            case "wall_slim_extend_1":
                tiles_map[tile]["neighbours"].extend(["e", "s", "w"])
            case "wall_slim_single_1":
                tiles_map[tile]["neighbours"].extend(["n", "e", "s", "w"])
            case "wall_slim_tip_1":
                tiles_map[tile]["neighbours"].extend(["n", "e", "s", "w"])
            case "wall_straight_1":
                tiles_map[tile]["neighbours"].extend(["e", "s", "w"])
            case "wall_straight_2":
                tiles_map[tile]["neighbours"].extend(["e", "s", "w"])
            case "water_concave_1":
                tiles_map[tile]["neighbours"].extend(["n", "w"])
            case "water_convex_1":
                tiles_map[tile]["neighbours"].extend(["n", "e", "s", "w"])
            case "water_extend_1":
                tiles_map[tile]["neighbours"].extend(["n", "e", "s", "w"])
            case _:
                tiles_map[tile]["neighbours"].extend([])

    for tile in tiles_map:
        print(tile, " ", tiles_map[tile])
