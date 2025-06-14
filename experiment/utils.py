import random
import json
import os


SESSION1_OBJECTS = [
    "1backpack",
    "1computer",
    "1fish",
    "1hair",
    "1table",
    "1key",
    "1lettuce",
    "1boat",
]

SESSION2_OBJECTS = [
    "2beach",
    "2carrot",
    "2chair",
    "2drill",
    "2hand",
    "2teapot",
    "2tree",
    "2turkey",
]


def get_permutation(subject_id: str, n: int = 8):
    """Return a permutation for the subject, creating one if needed."""
    fname = f"perm_{subject_id}.json"
    if os.path.exists(fname):
        with open(fname, "r") as f:
            perm = json.load(f)
    else:
        perm = list(range(n))
        random.shuffle(perm)
        with open(fname, "w") as f:
            json.dump(perm, f)
    return perm
