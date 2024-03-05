import PIL.Image as Image

tiles_map = {
    "w": {
        "image": Image.open("tiles/w.png"),
        "available": True,
        "weight": 50,
        "slots": {
            "n": ["w", "w-ur", "w-u", "w-ul"],
            "e": ["w", "w-dr", "w-ur", "w-r"],
            "s": ["w", "w-dr", "w-d", "w-dl"],
            "w": ["w", "w-dl", "w-ul", "w-l"],
        },
    },
    "w-dr": {
        "image": Image.open("tiles/w-dr.png"),
        "available": True,
        "weight": 5,
        "slots": {
            "n": ["w", "w-ur", "w-ul", "w-u"],
            "e": ["w-d", "w-dl", "w-urdl", "r-ul"],
            "s": ["w-ur", "r-ul", "w-urdl", "w-r"],
            "w": ["w", "w-ul", "w-dl", "w-l"]
        }
    },
    "w-ur": {
        "image": Image.open("tiles/w-ur.png"),
        "available": True,
        "weight": 5,
        "slots": {
            "n": ["w-dr", "w-r", "r-dl", "w-uldr"],
            "e": ["r-dl", "w-u", "w-uldr", "w-ul"],
            "s": ["w", "w-dl", "w-d", "w-dr"],
            "w": ["w", "w-ul", "w-l"],
        }
    },
    "w-r": {
        "image": Image.open("tiles/w-r.png"),
        "available": True,
        "weight": 5,
        "slots": {
            "n": ["w-dr", "w-uldr", "w-r", "r-dl"],
            "e": ["r", "r-dr", "r-ur", "w-l"],
            "s": ["w-ur", "w-urdl", "w-r", "r-ul"],
            "w": ["w", "w-dl", "w-ul", "w-l"]
        }
    },
    "w-ul": {
        "image": Image.open("tiles/w-ul.png"),
        "available": True,
        "weight": 5,
        "slots": {
            "n": ["w-l", "w-dl", "w-urdl", "r-dr"],
            "e": ["w", "w-dr", "w-ur", "w-r"],
            "s": ["w", "w-dl", "w-dr", "w-d"],
            "w": ["w-ur", "w-urdl", "w-u", "r-dr"]
        }
    },
    "w-uldr": {
        "image": Image.open("tiles/w-uldr.png"),
        "available": True,
        "weight": 5,
        "slots": {
            "n": ["w-l", "r-dr", "w-dl", "w-urdl"],
            "e": ["w-urdl", "w-dl", "w-d", "r-ul"],
            "s": ["w-urdl", "w-r", "w-ur", "r-ul"],
            "w": ["w-u", "w-ur", "r-dr", "w-urdl"]
        }
    },
    "w-u": {
        "image": Image.open("tiles/w-u.png"),
        "available": True,
        "weight": 5,
        "slots": {
            "n": ["r", "r-ul", "r-ur", "w-d"],
            "e": ["w-uldr", "w-ul", "w-u", "r-dl"],
            "s": ["w", "w-dl", "w-d", "w-dr"],
            "w": ["w-urdl", "w-ur", "w-u", "w-dr"]
        }
    },
    "r-dl": {
        "image": Image.open("tiles/r-dl.png"),
        "available": False,
        "weight": 1,
        "slots": {
            "n": ["r", "w-d", "r-ul", "r-ur"],
            "e": ["r", "w-l", "r-dr", "r-ur"],
            "s": ["w-urdl", "w-ur", "r-ul", "w-r"],
            "w": ["w-u", "r-dr", "w-urdl", "w-ur"]
        }
    },
    "w-dl": {
        "image": Image.open("tiles/w-dl.png"),
        "available": True,
        "weight": 5,
        "slots": {
            "n": ["w", "w-ul", "w-ur", "w-u"],
            "e": ["w", "w-ur", "w-dr", "w-r"],
            "s": ["w-ul", "w-uldr", "w-l", "r-ur"],
            "w": ["w-dr", "w-d", "w-uldr", "r-ur"]
        }
    },
    "w-d": {
        "image": Image.open("tiles/w-d.png"),
        "available": True,
        "weight": 5,
        "slots": {
            "n": ["w", "w-ul", "w-ur", "w-u"],
            "e": ["w-d", "r-ul", "w-urdl", "w-dl"],
            "s": ["r", "r-dl", "r-dr", "w-u"],
            "w": ["w-dr", "w-d", "r-ur", "w-uldr"]
        }
    },
    "w-urdl": {
        "image": Image.open("tiles/w-urdl.png"),
        "available": True,
        "weight": 5,
        "slots": {
            "n": ["w-uldr", "w-r", "w-dr", "r-dl"],
            "e": ["w-u", "r-dl", "w-uldr", "w-ul"],
            "s": ["w-l", "r-ur", "w-uldr", "w-ul"],
            "w": ["w-d", "r-ur", "r-ur", "w-uldr"]
        }
    },
    "r-ul": {
        "image": Image.open("tiles/r-ul.png"),
        "available": False,
        "weight": 1,
        "slots": {
            "n": ["w-r", "r-dl", "w-uldr", "w-dr"],
            "e": ["r", "r-dr", "r-ur", "w-l"],
            "s": ["r", "r-dl", "r-dr", "w-u"],
            "w": ["w-d", "r-ur", "w-uldr", "w-dr"]
        }
    },
    "w-l": {
        "image": Image.open("tiles/w-l.png"),
        "available": True,
        "weight": 5,
        "slots": {
            "n": ["w-dl", "w-l", "w-urdl", "r-dr"],
            "e": ["w", "w-ur", "w-dr", "w-r"],
            "s": ["w-l", "w-ul", "w-uldr", "r-ur"],
            "w": ["r", "r-ul", "r-dl", "w-r"]
        }
    },
    "r-ur": {
        "image": Image.open("tiles/r-ur.png"),
        "available": False,
        "weight": 1,
        "slots": {
            "n": ["w-l", "r-dr", "w-urdl", "w-dl"],
            "e": ["w-d", "w-urdl", "w-dl", "r-ul"],
            "s": ["r", "r-dl", "r-dr", "w-u"],
            "w": ["r", "r-dl", "r-ul", "w-r"]
        }
    },
    "r-dr": {
        "image": Image.open("tiles/r-dr.png"),
        "available": False,
        "weight": 1,
        "slots": {
            "n": ["r", "r-ul", "r-ur", "w-d"],
            "e": ["w-u", "r-dl", "w-uldr", "w-ul"],
            "s": ["w-l", "w-uldr", "w-ul", "r-ur"],
            "w": ["r", "w-r", "r-ul", "r-dl"]
        }
    },
    "r": {
        "image": Image.open("tiles/r.png"),
        "available": False,
        "weight": 1,
        "slots": {
            "n": ["r", "r-ul", "r-ur", "w-d"],
            "e": ["r", "r-ur", "r-dr", "w-l"],
            "s": ["r", "r-dl", "r-dr", "w-u"],
            "w": ["r", "r-dl", "r-ul", "w-r"]
        }
    }
}


def find_neighbours(tile, n, col, rows):
    row = n // col
    neighbours = []
    maxi = rows * col
    if tile == "w":
        neighbours.extend([n - 1, n + 1, n - col, n + col])
    if tile == "w-dr":
        neighbours.extend([n - 1, n + 1, n - col, n + col])
    if tile == "w-dl":
        neighbours.extend([n - 1, n + 1, n - col, n + col])
    if tile == "w-ur":
        neighbours.extend([n - 1, n + 1, n - col, n + col])
    if tile == "w-ul":
        neighbours.extend([n - 1, n + 1, n - col, n + col])
    if tile == "w-urdl":
        neighbours.extend([n - 1, n + 1, n - col, n + col])
    if tile == "w-uldr":
        neighbours.extend([n - 1, n + 1, n - col, n + col])
    if tile == "w-u":
        neighbours.extend([n - 1, n + 1, n + col])
    if tile == "w-d":
        neighbours.extend([n - 1, n + 1, n - col])
    if tile == "w-l":
        neighbours.extend([n + 1, n - col, n + col])
    if tile == "w-r":
        neighbours.extend([n - 1, n - col, n + col])
    if tile == "r-ul":
        neighbours.extend([n - 1, n - col])
    if tile == "r-ur":
        neighbours.extend([n + 1, n - col])
    if tile == "r-dr":
        neighbours.extend([n + 1, n + col])
    if tile == "r-dl":
        neighbours.extend([n - 1, n + col])

    if n == (row + 1) * col - 1:
        neighbours = list(filter(lambda x: 0 <= x < maxi and x != n + 1, neighbours))
    elif n == row * col:
        neighbours = list(filter(lambda x: 0 <= x < maxi and x != n - 1, neighbours))
    else:
        neighbours = list(filter(lambda x: 0 <= x < maxi, neighbours))

    return neighbours
