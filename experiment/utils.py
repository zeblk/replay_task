import random
import json
import os


SESSION1_OBJECTS = [
    "soccer_ball",
    "rose",
    "shirt",
    "car",
    "door",
    "phone",
    "apple",
    "cat",
]

SESSION2_OBJECTS = [
    "basketball",
    "sunflower",
    "jacket",
    "bicycle",
    "chair",
    "camera",
    "banana",
    "dog",
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
