import random
import json
import os
import math


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

TRAINING_OBJECTS = [
    "3papaya",
    "3broccoli",
    "3eggplant",
    "3strawberry",
    "3banana",
    "3fig",
    "3asparagus",
    "3pineapple",
]

def get_pos_and_seq(state_name: str):
    if 'p' in state_name:
        seq = 2
        poses = {'Wp': 1, 'Xp': 2, 'Yp': 3, 'Zp': 4}
        pos = poses[state_name]
    else:
        seq = 1
        poses = {'W': 1, 'X': 2, 'Y': 3, 'Z': 4}
        pos = poses[state_name]
    return pos, seq

def get_scrambled_pos_and_seq(scrambled_state: int):
    pos = (scrambled_state % 4) + 1
    seq = math.floor(scrambled_state / 4) + 1
    return pos, seq


def ordinal_string(n: int) -> str:
    """ Convert an integer to its ordinal representation as a string. """
    # Special case for teens (11th, 12th, 13th, ...)
    if 10 <= (n % 100) <= 20:
        suffix = 'th'
    else:
        # Otherwise use the last digit to determine suffix
        last = n % 10
        if last == 1:
            suffix = 'st'
        elif last == 2:
            suffix = 'nd'
        elif last == 3:
            suffix = 'rd'
        else:
            suffix = 'th'
    return f"{n}{suffix}"


def get_scrambling_rule(subject_id: int):
    """
    Return the scrambling rule for the subject, retrieving it from a central
    file or creating a new one if needed.
    """
    # All rules are stored in a single file.
    fname = "scrambling_rules.json"
    all_rules = {}

    # Load the central database of rules if it exists.
    if os.path.exists(fname):
        with open(fname, "r") as f:
            # Handle case where the file might be empty.
            try:
                all_rules = json.load(f)
            except json.JSONDecodeError:
                all_rules = {}

    # Convert integer ID to a string for human readability of the JSON file.
    subject_str = 'subject_' + str(subject_id)
    
    # If the rule for this subject already exists, return it.
    if subject_str in all_rules:
        return all_rules[subject_str]

    # Otherwise, create a new rule because one doesn't exist for this subject.
    # Enforce the constraint that the scrambled sequence alternates between true sequence 1 and true sequence 2.
    start_with_seq_1 = random.choice([True, False])
    if start_with_seq_1:
        list_of_letters_1 = ['W', 'X', 'Y', 'Z']
        scrambled_positions_1 = random.sample([0, 2, 4, 6], len(list_of_letters_1))
        scrambling_rule_1 = dict(zip(list_of_letters_1, scrambled_positions_1))

        list_of_letters_2 = ['Wp', 'Xp', 'Yp', 'Zp']
        scrambled_positions_2 = random.sample([1, 3, 5, 7], len(list_of_letters_2))
        scrambling_rule_2 = dict(zip(list_of_letters_2, scrambled_positions_2))
    else:
        list_of_letters_1 = ['W', 'X', 'Y', 'Z']
        scrambled_positions_1 = random.sample([1, 3, 5, 7], len(list_of_letters_1))
        scrambling_rule_1 = dict(zip(list_of_letters_1, scrambled_positions_1))

        list_of_letters_2 = ['Wp', 'Xp', 'Yp', 'Zp']
        scrambled_positions_2 = random.sample([0, 2, 4, 6], len(list_of_letters_2))
        scrambling_rule_2 = dict(zip(list_of_letters_2, scrambled_positions_2))

    new_rule = {**scrambling_rule_1, **scrambling_rule_2}

    # Add the newly created rule to our collection and save it.
    all_rules[subject_str] = new_rule
    with open(fname, "w") as f:
        # Use indent for better human readability of the JSON file.
        json.dump(all_rules, f, indent=4)
        
    return new_rule



def get_object_mapping(subject_id: int):
    """
    Return the randomized state-to-image mapping for the subject, retrieving it from a central
    file or creating a new one if needed.
    """
    # All mappings are stored in a single file.
    fname = "object_mappings.json"
    all_mappings = {}

    # Load the central database of mappings if it exists.
    if os.path.exists(fname):
        with open(fname, "r") as f:
            # Handle case where the file might be empty.
            try:
                all_mappings = json.load(f)
            except json.JSONDecodeError:
                all_mappings = {}

    # Convert integer ID to a string for human readability of the JSON file.
    subject_str = 'subject_' + str(subject_id)

    # If the mapping for this subject already exists, return it.
    if subject_str in all_mappings:
        return all_mappings[subject_str]

    # Otherwise, create a new mapping because one doesn't exist for this subject.
    list_of_letters = ['W', 'X', 'Y', 'Z', 'Wp', 'Xp', 'Yp', 'Zp']
    list_of_images = random.sample(SESSION1_OBJECTS, len(SESSION1_OBJECTS))
    new_mapping = dict(zip(list_of_letters, list_of_images))

    # Add the newly created rule to our collection and save it.
    all_mappings[subject_str] = new_mapping
    with open(fname, "w") as f:
        # Use indent for better human readability of the JSON file.
        json.dump(all_mappings, f, indent=4)
        
    return new_mapping

