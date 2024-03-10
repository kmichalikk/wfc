tiles_map = {
    "w": {
        "coords": [32, 32, 96, 96],
        "weight": 20,
        "slots": {
            "n": ["w", "w-ur", "w-u", "w-ul"],
            "e": ["w", "w-dr", "w-ur", "w-r"],
            "s": ["w", "w-dr", "w-d", "w-dl"],
            "w": ["w", "w-dl", "w-ul", "w-l"],
        },
        "neighbours": ["n", "e", "s", "w"]
    },
    "w-dr": {
        "coords": [160, 32, 224, 96],
        "weight": 5,
        "slots": {
            "n": ["w", "w-ur", "w-ul", "w-u"],
            "e": ["w-d", "w-dl", "w-urdl", "r-ul"],
            "s": ["w-ur", "r-ul", "w-urdl", "w-r"],
            "w": ["w", "w-ul", "w-dl", "w-l"]
        },
        "neighbours": ["n", "e", "s", "w"]
    },
    "w-ur": {
        "coords": [288, 32, 352, 96],
        "weight": 5,
        "slots": {
            "n": ["w-dr", "w-r", "r-dl", "w-uldr"],
            "e": ["r-dl", "w-u", "w-uldr", "w-ul"],
            "s": ["w", "w-dl", "w-d", "w-dr"],
            "w": ["w", "w-ul", "w-dr", "w-l"],
        },
        "neighbours": ["n", "e", "s", "w"]
    },
    "w-r": {
        "coords": [416, 32, 480, 96],
        "weight": 3,
        "slots": {
            "n": ["w-dr", "w-uldr", "w-r", "r-dl"],
            "e": ["r", "r-dr", "r-ur", "w-l"],
            "s": ["w-ur", "w-urdl", "w-r", "r-ul"],
            "w": ["w", "w-dl", "w-ul", "w-l"]
        },
        "neighbours": ["n", "s", "w"]
    },
    "w-ul": {
        "coords": [32, 160, 96, 224],
        "weight": 5,
        "slots": {
            "n": ["w-l", "w-dl", "w-urdl", "r-dr"],
            "e": ["w", "w-dr", "w-ur", "w-r"],
            "s": ["w", "w-dl", "w-dr", "w-d"],
            "w": ["w-ur", "w-urdl", "w-u", "r-dr"]
        },
        "neighbours": ["n", "e", "s", "w"]
    },
    "w-uldr": {
        "coords": [160, 160, 224, 224],
        "weight": 2,
        "slots": {
            "n": ["w-l", "r-dr", "w-dl", "w-urdl"],
            "e": ["w-urdl", "w-dl", "w-d", "r-ul"],
            "s": ["w-urdl", "w-r", "w-ur", "r-ul"],
            "w": ["w-u", "w-ur", "r-dr", "w-urdl"]
        },
        "neighbours": ["n", "e", "s", "w"]
    },
    "w-u": {
        "coords": [288, 160, 352, 224],
        "weight": 3,
        "slots": {
            "n": ["r", "r-ul", "r-ur", "w-d"],
            "e": ["w-uldr", "w-ul", "w-u", "r-dl"],
            "s": ["w", "w-dl", "w-d", "w-dr"],
            "w": ["w-urdl", "w-ur", "w-u", "w-dr"]
        },
        "neighbours": ["e", "s", "w"]
    },
    "r-dl": {
        "coords": [416, 160, 480, 224],
        "weight": 5,
        "slots": {
            "n": ["r", "w-d", "r-ul", "r-ur"],
            "e": ["r", "w-l", "r-dr", "r-ur"],
            "s": ["w-urdl", "w-ur", "r-ul", "w-r"],
            "w": ["w-u", "r-dr", "w-urdl", "w-ur"]
        },
        "neighbours": ["e", "s"]
    },
    "w-dl": {
        "coords": [32, 288, 96, 352],
        "weight": 5,
        "slots": {
            "n": ["w", "w-ul", "w-ur", "w-u"],
            "e": ["w", "w-ur", "w-dr", "w-r"],
            "s": ["w-ul", "w-uldr", "w-l", "r-ur"],
            "w": ["w-dr", "w-d", "w-uldr", "r-ur"]
        },
        "neighbours": ["n", "e", "s", "w"]
    },
    "w-d": {
        "coords": [160, 288, 224, 352],
        "weight": 3,
        "slots": {
            "n": ["w", "w-ul", "w-ur", "w-u"],
            "e": ["w-d", "r-ul", "w-urdl", "w-dl"],
            "s": ["r", "r-dl", "r-dr", "w-u"],
            "w": ["w-dr", "w-d", "r-ur", "w-uldr"]
        },
        "neighbours": ["n", "e", "w"]
    },
    "w-urdl": {
        "coords": [288, 288, 352, 352],
        "weight": 2,
        "slots": {
            "n": ["w-uldr", "w-r", "w-dr", "r-dl"],
            "e": ["w-u", "r-dl", "w-uldr", "w-ul"],
            "s": ["w-l", "r-ur", "w-uldr", "w-ul"],
            "w": ["w-d", "r-ur", "w-dr", "w-uldr"]
        },
        "neighbours": ["n", "e", "s", "w"]
    },
    "r-ul": {
        "coords": [416, 288, 480, 352],
        "weight": 5,
        "slots": {
            "n": ["w-r", "r-dl", "w-uldr", "w-dr"],
            "e": ["r", "r-dr", "r-ur", "w-l"],
            "s": ["r", "r-dl", "r-dr", "w-u"],
            "w": ["w-d", "r-ur", "w-uldr", "w-dr"]
        },
        "neighbours": ["n", "w"]
    },
    "w-l": {
        "coords": [32, 416, 96, 480],
        "weight": 3,
        "slots": {
            "n": ["w-dl", "w-l", "w-urdl", "r-dr"],
            "e": ["w", "w-ur", "w-dr", "w-r"],
            "s": ["w-l", "w-ul", "w-uldr", "r-ur"],
            "w": ["r", "r-ul", "r-dl", "w-r"]
        },
        "neighbours": ["n", "e", "s"]
    },
    "r-ur": {
        "coords": [160, 416, 224, 480],
        "weight": 5,
        "slots": {
            "n": ["w-l", "r-dr", "w-urdl", "w-dl"],
            "e": ["w-d", "w-urdl", "w-dl", "r-ul"],
            "s": ["r", "r-dl", "r-dr", "w-u"],
            "w": ["r", "r-dl", "r-ul", "w-r"]
        },
        "neighbours": ["n", "e"]
    },
    "r-dr": {
        "coords": [288, 416, 352, 480],
        "weight": 5,
        "slots": {
            "n": ["r", "r-ul", "r-ur", "w-d"],
            "e": ["w-u", "r-dl", "w-uldr", "w-ul"],
            "s": ["w-l", "w-uldr", "w-ul", "r-ur"],
            "w": ["r", "w-r", "r-ul", "r-dl"]
        },
        "neighbours": ["e", "s"]
    },
    "r": {
        "coords": [416, 416, 480, 480],
        "weight": 1,
        "slots": {
            "n": ["r", "r-ul", "r-ur", "w-d"],
            "e": ["r", "r-ur", "r-dr", "w-l"],
            "s": ["r", "r-dl", "r-dr", "w-u"],
            "w": ["r", "r-dl", "r-ul", "w-r"]
        },
        "neighbours": []
    }
}
