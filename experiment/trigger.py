#!/usr/bin/env python
# -*- coding: utf-8 -*-

import csv
import datetime
import time
import sys
import json

import psychopy
import psychopy.parallel

from rich.console import Console
console = Console()

human_to_byte = {}
names = ["Socks", "Key", "Belt", "Pen", "Clock", "Book", "Grapes", "Comb"]
inserted = 1
for name in names:
    human_to_byte[f"Stim/{name}"] = (inserted << 1) | 1
    inserted += 1

for cue in ["neither", "first", "second"]:
    human_to_byte[f"Cue/{cue}"] = (inserted << 1) | 1
    inserted += 1

for name_1 in names:
    for name_2 in names:
        human_to_byte[f"Question/first_{name_1}/then_{name_2}"] = (inserted << 1) | 1
        inserted += 1

for answer in ["Yes", "No"]:
    for correct in ["Correct", "Incorrect"]:
        human_to_byte[f"Answer/{answer}/{correct}"] = (inserted << 1) | 1
        inserted += 1

human_to_byte["Test"] = (inserted << 1) | 1

class MetaPort:
    """Writes triggers to a file, and when a MEG is connected send it there"""
    i = 0
    run_type = ""

    def __init__(self, subject_ID, actual_meg):
        self.items_list = []
        self.is_connected = False
        self.actual_meg = actual_meg
        self.subject_ID = subject_ID
        self.file_handle = None

        self.fname = f"local_data/{self.subject_ID}_{datetime.datetime.now().strftime('%Y-%m-%dT%H%M%S')}.csv"
        self.file_handle = open(self.fname, 'w', encoding="utf-8")
        self.csvwriter = csv.writer(self.file_handle, delimiter=',')

        self.csvwriter.writerow(["idx", "human_event", "event_code", "event_code_binary", "py_time", "trial_i", "item_i", "run"])
        self.file_handle.flush()

        if self.actual_meg:
            try:
                self.actual_meg = psychopy.parallel.ParallelPort(16376)
            except RuntimeError:
                console.print("ERROR: could not connect to the parallel port 0x0378", style="red")
                sys.exit(1)
            self.actual_meg.setData(0)
            self.is_connected = True
        else:
            console.print("####################################################", style="magenta")
            console.print("# ONLY mock port in use, no actual trigger is sent #", style="magenta")
            console.print("#          IS THIS WHAT YOU WANT???                #", style="magenta")
            console.print("####################################################", style="magenta")

        console.print(f"Writing data to {self.fname}", style="green")

    def write(self, message):
        """Writes a dict to a file, possibly writes to triggers"""
        human_event = message["event_type"]
        if message["trial_i"] == -1:
            message["trial_i"] = None
        if message["item_i"] == -1:
            message["item_i"] = None
        if message["run"] == -1:
            message["run"] = None
        value = human_to_byte[human_event]
        if self.is_connected:
            self.actual_meg.setData(value)
            console.print(f"Sent the MEG: {human_event}, i.e. {value} / {value:>08b}")
            time.sleep(0.1)
            self.actual_meg.setData(0)
        else:
            console.print(f"Would have sent the MEG: {human_event}, i.e. value={value} which in binary is {value:>08b}")
        to_write = [self.i, human_event, value, f"{value:>08b}", datetime.datetime.now().timestamp(), message["trial_i"], message["item_i"], message["run"]]
        console.print(f"{to_write}")
        self.csvwriter.writerow(to_write)
        self.file_handle.flush()
        self.i = self.i + 1

    def close(self):
        """Ensures the MEG is back to 0, and closes the file handle"""
        if self.is_connected:
            self.actual_meg.setData(0)
        self.file_handle.close()

def main(ID, actual_meg=True):
    meg = MetaPort(ID, actual_meg)
    # logic
    meg.write({"event_type": "Cue/first", "trial_i": 0, "item_i": 0, "run": 1})
    meg.close()

if __name__ == "__main__":
    main(12, actual_meg=False)
