#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime
import time
import sys
import json

import psychopy
import psychopy.parallel

from .utils import SESSION2_OBJECTS

human_to_byte = {
    **{'W': 10, 'X': 11, 'Y': 12, 'Z': 13, 
       'Wp': 14, 'Xp': 15, 'Yp': 16, 'Zp': 17,
       'fixation': 20, 'quiz_text': 21, 'probe_state': 22, 
       'quiz_choices': 23, 'timeout_message': 24, 'feedback_message': 25,
       '2_press': 30, '1_press': 31, # applied_learning
       '1_press': 40, '2_press': 41 }, # Localizer
    **{name: 40+ix for (ix, name) in enumerate(SESSION2_OBJECTS)}, # images
    **{name[1:].capitalize(): 50+ix for (ix,name) in enumerate(SESSION2_OBJECTS)}, # text names of objects
    }

class MetaPort:
    """Writes triggers to console, and when MEG is connected also send it there"""

    def __init__(self, subject_ID, actual_meg):
        self.items_list = []
        self.is_connected = False
        self.actual_meg = actual_meg
        self.subject_ID = subject_ID

        if self.actual_meg:
            try:
                self.actual_meg = psychopy.parallel.ParallelPort(16376)
            except RuntimeError:
                print("ERROR: could not connect to the parallel port 0x0378")
                sys.exit(1)
            self.actual_meg.setData(0)
            self.is_connected = True
        else:
            print("####################################################")
            print("# ONLY mock port in use, no actual trigger is sent #")
            print("#          IS THIS WHAT YOU WANT???                #")
            print("####################################################")


    def write(self, message):
        """Writes a dict to a file, possibly writes to triggers"""
        
        value = human_to_byte[message]
        if self.is_connected:
            self.actual_meg.setData(value)
            print(f"Sent the MEG: {message}, i.e. {value} / {value:>08b}")
            time.sleep(0.1)
            self.actual_meg.setData(0)
        else:
            print(f"Would have sent the MEG: {message}, i.e. {value} / {value:>08b}")

    def close(self):
        """Ensures the MEG is back to 0"""
        if self.is_connected:
            self.actual_meg.setData(0)

