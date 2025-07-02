"""Utility functions for object mappings and scrambling rules."""

from __future__ import annotations

import json
import math
import os
from pathlib import Path
import random


def read_json(path: Path) -> dict:
    """Safely read JSON data from *path*, returning an empty dict on failure."""
    if not path.exists():
        return {}
    try:
        with path.open("r") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return {}


def write_json(path: Path, data: dict) -> None:
    """Write *data* to *path* in JSON format with human readable indentation."""
    with path.open("w") as f:
        json.dump(data, f, indent=4)



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

def get_pos_and_seq(state_name: str) -> tuple[int, int]:
    """Return the position and sequence index for a given state."""
    if "p" in state_name:
        seq = 2
        poses = {"Wp": 1, "Xp": 2, "Yp": 3, "Zp": 4}
        pos = poses[state_name]
    else:
        seq = 1
        poses = {"W": 1, "X": 2, "Y": 3, "Z": 4}
        pos = poses[state_name]
    return pos, seq

def get_scrambled_pos_and_seq(scrambled_state: int) -> tuple[int, int]:
    """Return the position and sequence for a scrambled state index."""
    pos = (scrambled_state % 4) + 1
    seq = math.floor(scrambled_state / 4) + 1
    return pos, seq

def pos_and_seq_to_state(pos: int, seq: int) -> str:
    if seq == 1:
        return ['W','X','Y','Z'][pos-1]
    elif seq == 2:
        return ['Wp','Xp','Yp','Zp'][pos-1]
    else:
        raise Exception('sequence must be 1 or 2')

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
    fname = Path("scrambling_rules.json")
    all_rules = read_json(fname)

    # Convert integer ID to a string for human readability of the JSON file.
    subject_str = 'subject_' + str(subject_id)
    
    # If the rule for this subject already exists, return it.
    if subject_str in all_rules:
        return all_rules[subject_str]

    # Otherwise, create a new rule because one doesn't exist for this subject.
    new_rule = create_random_mapping()

    # Add the newly created rule to our collection and save it.
    all_rules[subject_str] = new_rule
    write_json(fname, all_rules)
        
    return new_rule

def create_random_mapping():
    """
    Creates a random mapping from lettercodes to numbers 0-7 with constraints.
    
    Constraint: Within each scrambled sequence, we must alternate between the two true sequences.
    """
    true_sequence_1 = ['W', 'X', 'Y', 'Z']
    true_sequence_2 = ['Wp', 'Xp', 'Yp', 'Zp']
    
    # Start with all lettercodes available
    available_codes = true_sequence_1 + true_sequence_2
    mapping = {}
    
    # Track which subset each number belongs to
    number_subsets = {}
    
    # Process numbers in order, respecting constraints
    for num in range(8):
        if num == 0:
            # First number can go anywhere
            chosen_code = random.choice(available_codes)
        elif num == 4:
            # Number 4 can go anywhere (no constraint with 3)
            chosen_code = random.choice(available_codes)
        else:
            # For numbers 1,2,3,5,6,7 - check constraint with previous number
            prev_num = num - 1
            prev_subset = number_subsets[prev_num]
            
            # Must choose from the opposite subset
            if prev_subset == 'seq1':
                valid_codes = [code for code in available_codes if code in true_sequence_2]
            else:
                valid_codes = [code for code in available_codes if code in true_sequence_1]
            
            chosen_code = random.choice(valid_codes)
        
        # Update our tracking
        mapping[chosen_code] = num
        available_codes.remove(chosen_code)
        
        # Track which subset this number belongs to
        if chosen_code in true_sequence_1:
            number_subsets[num] = 'seq1'
        else:
            number_subsets[num] = 'seq2'
    
    return mapping


def get_object_mapping(subject_id: int, phase: str, force_new: bool=False) -> dict:
    """
    Return the randomized state-to-image mapping for the subject, retrieving it from a central
    file or creating a new one if needed.
    """
    # All mappings are stored in a single file.
    fname = Path("object_mappings.json")
    all_mappings = read_json(fname)

    # Convert integer ID to a string for human readability of the JSON file.
    subject_str = 'subject_' + str(subject_id)

    # If the mapping for this subject and phase already exists, return it.
    if (subject_str in all_mappings) and not force_new:
        if phase in all_mappings[subject_str]:
            return all_mappings[subject_str][phase]

    # Otherwise, create a new mapping because one doesn't exist for this subject.
    list_of_letters = ['W', 'X', 'Y', 'Z', 'Wp', 'Xp', 'Yp', 'Zp']
    
    if phase == 'training':
        list_of_images = random.sample(TRAINING_OBJECTS, len(TRAINING_OBJECTS))
    elif phase == 'structure_learning':
        list_of_images = random.sample(SESSION1_OBJECTS, len(SESSION1_OBJECTS))
    elif phase == 'applied_learning':
        list_of_images = random.sample(SESSION2_OBJECTS, len(SESSION2_OBJECTS))

    new_mapping = dict(zip(list_of_letters, list_of_images))

    # Add this subject to the mappings if not already present
    if subject_str not in all_mappings:
        all_mappings[subject_str] = dict()

    # Add the newly created rule to our collection and save it.
    all_mappings[subject_str][phase] = new_mapping

    write_json(fname, all_mappings)
        
    return new_mapping

