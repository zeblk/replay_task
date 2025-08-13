from __future__ import annotations

import argparse
import csv
import os
import random
import warnings
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict

import numpy as np
import pyglet
from psychopy import core, event, visual

from .utils import (
    get_object_mapping,
    get_pos_and_seq,
    get_scrambled_pos_and_seq,
    get_scrambling_rule,
    ordinal_string,
    pos_and_seq_to_state,
)

# Paths
HERE = Path(__file__).parent
IMAGES_DIR = HERE / "images"
WIN_WIDTH = 900
WIN_HEIGHT = 700

MESSAGE_DURATION = 1.0
SCRAMBLED_REPEATS = 5
OBJECT_DURATION = 0.9
REST_DURATION = 1.0
N_OBJECTS = 8
ISI = 1.0
ITI = 1.5
N_RUNS = 3

# For debugging
# MESSAGE_DURATION = 0.3
# SCRAMBLED_REPEATS = 5
# OBJECT_DURATION = 0.1
# REST_DURATION = .1
# N_OBJECTS = 8
# ISI = .1
# ITI = .1
# N_RUNS = 3

true_state_names = ['W', 'X', 'Y', 'Z', 'Wp', 'Xp', 'Yp', 'Zp']
scrambled_positions = [0, 1, 2, 3, 4, 5, 6, 7]

warnings.filterwarnings(
    "ignore",
    message="elementwise comparison failed.*",
    category=FutureWarning,
    module=r"psychopy\.visual\.shape"
)


@dataclass
class StructureLearning:
    """Structure Learning (Day 1) task from Liu et al (2019).
    Participants undergo three runs of training. Each run consists of showing both scrambled sequences three times.
    Each stimulus is onscreen for 1000 ms, with 500 ms between stimuli, and an extra 1000 ms of blank screen between sequences.
    After each run, participants are probed about the true (unscrambled) order.
    On each probe trial, the probe stimulus is presented in the center of the screen, and two other stimuli are presented below. 
    One of the two lower stimuli is selected from later in the same true sequence as the probe.
    The other lower stimulus is randomly selected either from earlier in the same true sequence as the probe,
    or from any position in the other true sequence. 
    Participants are asked to press the button (left or right) corresponding to the stimulus that is later
    in the same true sequence as the probe.
    For example, if X is the probe stimulus, and the two choice options are W and Z, then the correct answer is Z. 
    There are ten probe questions at the end of each run.
    No feedback is given during probe trials.
    """

    subject_id: int
    win: visual.Window = field(init=False)
    behavior_file: object = field(init=False)
    behavior_writer: csv.writer = field(init=False)
    scrambling_rule: Dict[str, int] = field(init=False)
    object_mapping: Dict[str, str] = field(init=False)
    object_stims: Dict[str, visual.ImageStim] = field(init=False)

    def __post_init__(self) -> None:
        self.scrambling_rule = get_scrambling_rule(self.subject_id)
        self.object_mapping = get_object_mapping(self.subject_id, 'structure_learning')
        self.win = visual.Window(color="black",  size=(WIN_WIDTH, WIN_HEIGHT), units="norm")
        # self.win = visual.Window(color="black", size=(1920, 1080), fullscr=True, units="norm", allowGUI=False,)
        event.globalKeys.clear()
        event.globalKeys.add(key="escape", func=self._exit)

        # open behavioral data file
        os.makedirs('behavior_data', exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_name = f"subject_{self.subject_id}_structure_learning_behavior_{timestamp}.csv"
        self.behavior_filename = os.path.join('behavior_data', file_name)
        self.behavior_file = open(self.behavior_filename, "w", newline="")

        self.behavior_writer = csv.writer(self.behavior_file)
        self.behavior_writer.writerow([
            "subject_id",
            "run_number",  # Added to track which run (1-3)
            "probe_stimulus_picture",    
            "probe_stimulus_true_state",
            "probe_stim_number",
            "probe_stim_seq",
            "correct_stimulus_picture",
            "correct_stimulus_true_state",
            "correct_stim_number",
            "correct_stim_seq",
            "incorrect_stimulus_picture",
            "incorrect_stimulus_true_state",
            "incorrect_stim_number",
            "incorrect_stim_seq",
            "correct_state_on_left",  # True = left, False = right
            "key_pressed", 
            "chosen_true_state", 
            "chosen_state_picture",
            "is_correct", 
            "reaction_time", 
        ])

        # pre-load images
        self.preload_images()
       
    def preload_images(self) -> None:
        """Helper method to load/reload images"""
        self.object_stims = {}
        for letter, obj_name in self.object_mapping.items():
            img_path = IMAGES_DIR / f"{obj_name}.png"
            self.object_stims[letter] = visual.ImageStim(self.win, image=str(img_path))

    def _exit(self):
        print("Esc detected: ending experiment...")
        self.close()
        core.quit()
        os._exit(0)

    def close(self) -> None:
        """Close open resources."""
        try:
            self.win.close()
            visual.Window._closeAllWindows()
        except Exception:
            pass
        try:
            self.behavior_file.close()
        except Exception:
            pass

    def get_object(self, obj_letter: str, size: tuple=(0.5, 0.5), pos: tuple=(0,0)):
        """Display an image corresponding to the specified object letter (W, X, Y, Z, Wp, Xp, Yp, Zp)."""
        # Specify the image size in 'norm' units. (1,1) would fill a quarter of the screen.
        stim = self.object_stims[obj_letter]
        
        # Squash the object horizontally to compensate for the aspect ratio of the window
        width, height = self.win.size
        a_r = width/height
        stim.size = (size[0]/a_r, size[1])

        stim.pos = pos
        return stim

    def reverse_state_lookup(self, scrambled_position):
        """ Finds the unscrambled state that maps to scrambled_position. """
        # Uses reverse dictionary lookup.
        return [key for key, value in self.scrambling_rule.items() if value == scrambled_position][0]

    def run(self):
        
        def left_right_msg(available_keys: list):
            """ Draw left/right navigation instructions for participants """
            if 'left' in available_keys:
                visual.TextStim(self.win, text='< left', color='white', height=0.05, pos=(-.9,-.9)).draw()
            if 'space' in available_keys:
                visual.TextStim(self.win, text='space to continue', color='white', height=0.05, pos=(0,-.9)).draw()
            if 'right' in available_keys:
                visual.TextStim(self.win, text='right >', color='white', height=0.05, pos=(.9,-.9)).draw()
            self.win.flip()
            keys = event.waitKeys(keyList=available_keys + ['escape'])
            return keys

        def screen1():
            visual.TextStim(self.win, text='Now, you will apply the rule you learned to unscramble a new set of pictures.', height=0.1, pos=(0,0)).draw()

        def screen2():
            visual.TextStim(self.win, text='First, you will see the 1st scrambled sequence repeated 3 times in a row.', height=0.1, pos=(0,.5)).draw()
            visual.TextStim(self.win, text='Then, you will see the 2nd scrambled sequence repeated 3 times in a row.', height=0.1, pos=(0,0)).draw()
            visual.TextStim(self.win, text='Finally, we will ask quiz questions about the true (unscrambled) order.', height=0.1, pos=(0,-.5)).draw()
            
        def screen3():
            visual.TextStim(self.win, text='Each quiz question will show one picture at the top, and ' + \
                'two pictures below, like this.', height=0.1, pos=(0,.0)).draw()
            self.get_object(self.reverse_state_lookup(0), size=(0.5,0.5), pos=(0,.5)).draw()
            self.get_object(self.reverse_state_lookup(1), size=(0.3,0.3), pos=(-.5,-.5)).draw()
            self.get_object(self.reverse_state_lookup(2), size=(0.3,0.3), pos=(.5,-.5)).draw()
        
        def screen4():
            visual.TextStim(self.win, text='This entire process will repeat 3 times.', height=0.1, pos=(0,.5)).draw()
            visual.TextStim(self.win, text='On each repeat, we will reshuffle the pictures.', height=0.1, pos=(0,0)).draw()
            visual.TextStim(self.win, text='*Remember, the rule stays the same*', height=0.1, pos=(0,-.5)).draw()
            
        def screen5():
            visual.TextStim(self.win, text='You can choose one of the two pictures below.', height=0.08, pos=(0,.15)).draw()
            visual.TextStim(self.win, text='The correct choice is the picture that is *later in the same true sequence* ' + \
                'as the picture on top.', height=0.08, pos=(0,-.17)).draw()
            self.get_object(self.reverse_state_lookup(0), size=(0.5,0.5), pos=(0,.5)).draw()
            self.get_object(self.reverse_state_lookup(1), size=(0.3,0.3), pos=(-.5,-.5)).draw()
            self.get_object(self.reverse_state_lookup(2), size=(0.3,0.3), pos=(.5,-.5)).draw()

        def scrambled_sequences_screen(which_seq: int):
            if which_seq == 1:
                sp_list = [0, 1, 2, 3]
            elif which_seq == 2:
                sp_list = [4, 5, 6, 7]

            for scrambled_position in sp_list:
                # Fixation
                visual.TextStim(self.win, text='+', height=0.3, pos=(0,0)).draw()
                self.win.flip()
                core.wait(ISI)

                # Object
                state_name = self.reverse_state_lookup(scrambled_position)
                self.get_object(state_name, size=(0.5,0.5), pos=(0,0)).draw()
                self.win.flip()
                core.wait(OBJECT_DURATION)

            self.win.flip()
            core.wait(ITI)


        def quiz_screen(run_number: int):

            # Select the probe state
            prob_seq = random.choice([1,2])
            prob_pos = random.choice([1,2,3])
            probe_state = pos_and_seq_to_state(pos=prob_pos, seq=prob_seq)
            
            # Select the correct choice option
            correct_seq = prob_seq
            correct_pos = random.choice(range(prob_pos+1,5))
            correct_state = pos_and_seq_to_state(pos=correct_pos, seq=correct_seq)

            # Select the incorrect choice option
            if prob_pos == 1:
                # if the probe is at the first position, then the incorrect choice must be from the other sequence
                incorrect_seq = 3-prob_seq
            else:
                # otherwise we can choose a sequence randomly
                incorrect_seq = random.choice([1,2])

            if incorrect_seq == prob_seq:
                # if they're in the same sequence, then the incorrect choice must come earlier
                incorrect_pos = random.choice(range(1,prob_pos))
            else:
                # if they're in different sequences, then the incorrect choice can come from any position
                incorrect_pos = random.choice([1,2,3,4])

            incorrect_state = pos_and_seq_to_state(pos=incorrect_pos, seq=incorrect_seq)

            # Randomly decide whether to put the correct choice on the left side of the screen
            correct_on_left = random.choice([True,False])

            # Draw the question
            visual.TextStim(self.win, text='Which comes later in the same true sequence?', 
                            height=0.07, pos=(0,-.2)).draw()

            # Draw the probe stimulus
            self.get_object(probe_state, size=(0.5,0.5), pos=(0,.5)).draw()

            # Draw the two choices
            self.get_object(correct_state, size=(0.3,0.3), pos=(-(2*int(correct_on_left)-1)*.5,-.5)).draw()
            self.get_object(incorrect_state, size=(0.3,0.3), pos=((2*int(correct_on_left)-1)*.5,-.5)).draw()
            visual.TextStim(self.win, text='(Press left)', height=0.07, pos=(-.5,-.68)).draw()
            visual.TextStim(self.win, text='(Press right)', height=0.07, pos=(.5,-.68)).draw()
            self.win.flip()
            clock = core.Clock()
            key_data = event.waitKeys(keyList=["left", "right", "escape"], timeStamped=clock)
            key, rt = key_data[0]
            sj_correctness = ((key == "left") and correct_on_left) or ((key == "right") and (not correct_on_left))
            chosen_state = correct_state if (key == "left" and correct_on_left or key=="right" and not correct_on_left) else incorrect_state
            chosen_obj = self.object_mapping[chosen_state][1:]

            # State mapping
            state_map = {'W':1, 'X':2, 'Y':3, 'Z':4, 'Wp':5, 'Xp':6, 'Yp':7, 'Zp':8}

            # Probe info
            probe_stim_number = state_map[probe_state]
            probe_stim_seq = 1 if probe_stim_number <= 4 else 2

            # Correct
            correct_stim_picture = self.object_mapping[correct_state][1:]
            correct_stim_number = state_map[correct_state]
            correct_stim_seq = 1 if correct_stim_number <= 4 else 2

            # Right
            incorrect_stim_picture = self.object_mapping[incorrect_state][1:]
            incorrect_stim_number = state_map[incorrect_state]
            incorrect_stim_seq = 1 if incorrect_stim_number <= 4 else 2

            # Record data to behavior file
            self.behavior_writer.writerow([
                self.subject_id,
                run_number + 1,  # Add 1 to make it 1-indexed (1, 2, 3) instead of 0-indexed
                self.object_mapping[probe_state][1:],  # probe_picture
                probe_state,
                probe_stim_number,
                probe_stim_seq,
                correct_stim_picture, # correct_picture
                correct_state,
                correct_stim_number,
                correct_stim_seq,
                incorrect_stim_picture,  # incorrect_picture
                incorrect_state,
                incorrect_stim_number,
                incorrect_stim_seq,
                int(correct_on_left),
                key,
                chosen_state,
                chosen_obj,  # picture
                int(sj_correctness),
                rt,
            ])
            self.behavior_file.flush()

        ####################### Do the intro

        intro_screens = [screen1, screen2, screen3, screen4, screen5]
        available_keys = [['right'], ['left','right'], ['left','right'], ['left','right'], ['left', 'space']]
        screen_ix = 0
        done = False
        while not done:
            # Draw the current screen
            intro_screens[screen_ix]()
            keys = left_right_msg(available_keys[screen_ix])
            
            if keys[0] == 'left':
                screen_ix -= 1
            elif keys[0] == 'space':
                done = True
            elif keys[0] == 'right':
                screen_ix += 1
            screen_ix = np.maximum(np.minimum(screen_ix, len(intro_screens)-1), 0)

        ####################### Do the structure learning task

        # Loop through the runs
        for run in range(N_RUNS):
            # Reshuffle pictures for each run (except the first)
            if run > 0:
                # Get new object mapping (pictures change but rule stays the same)
                self.object_mapping = get_object_mapping(self.subject_id, 'structure_learning', force_new=True)
                # Reload images with new mapping
                self.preload_images()
            
            # Show scrambled sequence 1 three times (no prompt)
            for repeat in range(3):
                scrambled_sequences_screen(which_seq = 1)

            # Show scrambled sequence 2 three times (no prompt)
            for repeat in range(3):
                scrambled_sequences_screen(which_seq = 2)

            # Quiz phase
            for probe_ix in range(10):
                quiz_screen(run_number=run)  # Pass run number to quiz_screen
                self.win.flip()
                core.wait(ISI)

        visual.TextStim(self.win, text="All done.", height=0.1, pos=(0,0.0)).draw()
        visual.TextStim(self.win, text="Press space to exit", height=0.07, pos=(0,-0.5)).draw()
        self.win.flip()
        event.waitKeys(keyList=['space'])

        self.close()
        core.quit()


def main() -> None:
    """Entry point for running the experiment."""
    parser = argparse.ArgumentParser(description="Task 2 from Liu et al (2019) cell")
    parser.add_argument("subject_id", type=int, help="Unique subject identifier")
    args = parser.parse_args()

    session = StructureLearning(args.subject_id)
    session.run()


if __name__ == "__main__":
    main()