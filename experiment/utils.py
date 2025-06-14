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


def get_scrambling_rule(subject_id: str, n: int = 8):
    """Return the scrambling rule for the subject, creating one if needed."""
    fname = f"scrambling_rule_{subject_id}.json"
    if os.path.exists(fname):
        with open(fname, "r") as f:
            scrambling_rule = json.load(f)
    else:
        list_of_letters = ['W', 'X', 'Y', 'Z', 'Wp', 'Xp', 'Yp', 'Zp']
        list_of_letters_2 = random.sample(list_of_letters, len(list_of_letters))
        scrambling_rule = dict(zip(list_of_letters, list_of_letters_2))

        with open(fname, "w") as f:
            json.dump(scrambling_rule, f)
    return scrambling_rule

def get_object_mapping(subject_id: str, n: int = 8):
    """Return the randomized state-to-image mapping for the subject, creating one if needed."""
    fname = f"object_mapping_{subject_id}.json"
    if os.path.exists(fname):
        with open(fname, "r") as f:
            object_mapping = json.load(f)
    else:
        list_of_letters = ['W', 'X', 'Y', 'Z', 'Wp', 'Xp', 'Yp', 'Zp']
        list_of_images = random.sample(SESSION1_OBJECTS, len(SESSION1_OBJECTS))
        object_mapping = dict(zip(list_of_letters, list_of_images))

        with open(fname, "w") as f:
            json.dump(object_mapping, f)
    return object_mapping    