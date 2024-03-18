import csv

tiles_map = {}
with (open('slots.csv', 'r') as file):
    reader = csv.reader(file)
    first_row = next(reader)

    for tile in first_row:
        if len(tile) > 1:
            tiles_map[tile.lstrip()] = {
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
            if row[i] == "1":
                tiles_map[row[0].lstrip()[:-2]]["slots"][row[0][-1]].add(first_row[i].lstrip())

    for tile in tiles_map:
        if "empty" in tile:
            tiles_map[tile]["weight"] = 20
        elif "water" in tile:
            tiles_map[tile]["weight"] = 8
        elif "slim" in tile:
            tiles_map[tile]["weight"] = 2
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
            case "wall_straight_1_1":
                tiles_map[tile]["neighbours"].extend(["e", "s", "w"])
            case "wall_straight_2_1":
                tiles_map[tile]["neighbours"].extend(["e", "s", "w"])
            case "water_concave_1":
                tiles_map[tile]["neighbours"].extend(["n", "w"])
            case "water_convex_1":
                tiles_map[tile]["neighbours"].extend(["n", "e", "s", "w"])
            case "water_extend_1":
                tiles_map[tile]["neighbours"].extend(["n", "e", "s", "w"])
            case _:
                tiles_map[tile]["neighbours"].extend([])

        def rotate_tile_slots(tile_name: str, alignment: int):
            digit = int(tile_name[-1])
            digit = digit + alignment
            if digit > 4:
                digit %= 4
            return tile_name[:-1] + str(digit)

        tile_rotation_map = {
            "n": ["n", "e", "s", "w"],
            "e": ["e", "s", "w", "n"],
            "s": ["s", "w", "n", "e"],
            "w": ["w", "n", "e", "s"],
        }

        for tile in tiles_map:
            if tile[-1] != "1":
                continue

            # for all rotated tile variants, assign slots with correct rotations/alignments
            # relative to them
            for rot in [1, 2, 3]:
                for alignment in ["n", "e", "s", "w"]:
                    new_alignment = tile_rotation_map[alignment][rot]
                    tiles_map[tile[:-1] + str(rot+1)]["slots"][new_alignment] \
                        = [rotate_tile_slots(neighbour, rot) for neighbour in tiles_map[tile]["slots"][alignment]]

            # todo: verify if it works as intended given all rotations
            if tiles_map[tile]["neighbours"] == ["n", "e", "s", "w"]:
                tiles_map[tile[:-1] + "2"]["neighbours"] = ["n", "e", "s", "w"]
                tiles_map[tile[:-1] + "3"]["neighbours"] = ["n", "e", "s", "w"]
                tiles_map[tile[:-1] + "4"]["neighbours"] = ["n", "e", "s", "w"]
            if tiles_map[tile]["neighbours"] == ["e", "s"]:
                tiles_map[tile[:-1] + "2"]["neighbours"] = ["s", "w"]
                tiles_map[tile[:-1] + "3"]["neighbours"] = ["w", "n"]
                tiles_map[tile[:-1] + "4"]["neighbours"] = ["n", "e"]
            if tiles_map[tile]["neighbours"] == ["e", "s", "w"]:
                tiles_map[tile[:-1] + "2"]["neighbours"] = ["s", "w", "n"]
                tiles_map[tile[:-1] + "3"]["neighbours"] = ["w", "n", "s"]
                tiles_map[tile[:-1] + "4"]["neighbours"] = ["n", "e", "s"]
            if tiles_map[tile]["neighbours"] == ["n", "w"]:
                tiles_map[tile[:-1] + "2"]["neighbours"] = ["e", "n"]
                tiles_map[tile[:-1] + "3"]["neighbours"] = ["s", "e"]
                tiles_map[tile[:-1] + "4"]["neighbours"] = ["w", "n"]

print("tiles_map={")
for tile in tiles_map:
    print("'" + tile.lstrip().rstrip() + "':", tiles_map[tile], ",")
print("}")
