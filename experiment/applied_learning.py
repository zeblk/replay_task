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


MESSAGE_DURATION = 1.0
SCRAMBLED_REPEATS = 5
OBJECT_DURATION = 0.9
REST_DURATION = 1.0
N_OBJECTS = 8
ISI = 0.9
ITI = 1.5
N_RUNS = 3
N_REPEATS = 3
PROBE_ALONE_DURATION = 5
CHOICE_DURATION = 0.6

true_state_names = ['W', 'X', 'Y', 'Z', 'Wp', 'Xp', 'Yp', 'Zp']
scrambled_positions = [0, 1, 2, 3, 4, 5, 6, 7]

warnings.filterwarnings(
    "ignore",
    message="elementwise comparison failed.*",
    category=FutureWarning,
    module=r"psychopy\.visual\.shape"
)


@dataclass
class AppliedLearning:
    """Applied Learning (Day 2) task from Liu et al (2019).
    There were three runs of Applied Learning.
    There were two phases in each run.
    Each phase comprised four images with each stimulus presented for 900 ms, followed by an inter-stimulus interval (ISI) of 900 ms. 
    Each phase was repeated three times, then followed by the next phase.
    Each run was followed by multiple choice questions without feedback.
    The probe stimulus appeared alone for 5 s, and then the two candidate successor images appeared.
    One image came from later in the same sequence as the probe.
    The other was preceding in the same sequence with 33% probability; and from the other sequence with 66% probability.
    Participants had 600 ms to make a choice.
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
        self.object_mapping = get_object_mapping(self.subject_id, 'applied_learning')
        self.win = visual.Window(color="black", size=(1024, 768), fullscr=False, units="norm")
        event.globalKeys.clear()
        event.globalKeys.add(key="escape", func=self._exit)

        # open behavioral data file
        os.makedirs('behavior_data', exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_name = f"subject_{self.subject_id}_applied_learning_behavior_{timestamp}.csv"
        self.behavior_filename = os.path.join('behavior_data', file_name)
        self.behavior_file = open(self.behavior_filename, "w", newline="")

        self.behavior_writer = csv.writer(self.behavior_file)
        self.behavior_writer.writerow([
            "probe_stimulus_true_state",
            "probe_stimulus_picture",
            "left_stimulus_true_state",
            "left_stimulus_picture",
            "right_stimulus_true_state",
            "right_stimulus_picture",
            "key_pressed",
            "chosen_true_state",
            "is_correct",
            "reaction_time",
        ])

        # pre-load images
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

        def quiz_screen():

            # Select the probe state
            prob_seq = random.choice([1,2])
            prob_pos = random.choice([1,2,3])
            probe_state = pos_and_seq_to_state(pos=prob_pos, seq=prob_seq)
            
            # Select the correct choice option
            correct_seq = prob_seq
            correct_pos = random.choice(range(prob_pos+1,5))
            correct_state = pos_and_seq_to_state(pos=correct_pos, seq=correct_seq)

            # Select the incorrect choice option  (TODO: make sure it's 33% prob of being from the same sequence)
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
            visual.TextStim(self.win, text='When the options appear, choose the one that comes later in the same true sequence.', 
                            height=0.07, pos=(0,0)).draw()

            # Draw the probe stimulus
            self.get_object(probe_state, size=(0.5,0.5), pos=(0,.5)).draw()

            # Present the probe stimulus alone for a long duration
            self.win.flip()
            core.wait(PROBE_ALONE_DURATION)

            # Draw the two choices
            self.get_object(correct_state, size=(0.5,0.5), pos=(-(2*int(correct_on_left)-1)*.5,0)).draw()
            self.get_object(incorrect_state, size=(0.5,0.5), pos=((2*int(correct_on_left)-1)*.5,0)).draw()
            visual.TextStim(self.win, text='(Press left)', height=0.07, pos=(-.5,-.5)).draw()
            visual.TextStim(self.win, text='(Press right)', height=0.07, pos=(.5,-.5)).draw()
            self.win.flip()
            clock = core.Clock()
            key_data = event.waitKeys(maxWait=CHOICE_DURATION, keyList=["left", "right", "escape"], timeStamped=clock)

            if not key_data:
                # Subject timed out
                key = None
                rt = None
                sj_correctness = None
                chosen_state = None
                chosen_obj = None

                visual.TextStim(self.win, text='Too slow. Respond faster.', height=0.1, pos=(0,0)).draw()
                self.win.flip()
                core.wait(2.0)
            else:
                key, rt = key_data[0]
                sj_correctness = ((key == "left") and correct_on_left) or ((key == "right") and (not correct_on_left))
                chosen_state = correct_state if (key == "left" and correct_on_left or key=="right" and not correct_on_left) else incorrect_state
                chosen_obj = self.object_mapping[chosen_state][1:]

            # Record data to behavior file
            self.behavior_writer.writerow([
                probe_state,
                self.object_mapping[probe_state][1:],
                correct_state,
                self.object_mapping[correct_state][1:],
                incorrect_state,
                self.object_mapping[incorrect_state][1:],
                correct_on_left,
                key,
                chosen_state,
                sj_correctness,
                rt,
            ])
            self.behavior_file.flush()


        ####################### Do the applied learning task
        visual.TextStim(self.win, text='Now you will see today\'s stimuli in their scrambled order.', height=0.1, pos=(0,.15)).draw()
        visual.TextStim(self.win, text='Press space when ready.', height=0.1, pos=(0,-.15)).draw()
        self.win.flip()
        event.waitKeys(keyList=['space'])

        # Do four runs
        for run in range(N_RUNS):
            # Phase 1
            for repeat in range(N_REPEATS):
                visual.TextStim(self.win, text='Press space when you\'re ready to see the 1st scrambled sequence.', 
                                height=0.1, pos=(0,0)).draw()
                self.win.flip()
                event.waitKeys(keyList=["space"])
                scrambled_sequences_screen(which_seq = 1)

            # Phase 2
            for repeat in range(N_REPEATS):
                visual.TextStim(self.win, text='Press space when you\'re ready to see the 2nd scrambled sequence.', 
                                height=0.1, pos=(0,0)).draw()
                self.win.flip()
                event.waitKeys(keyList=["space"])
                scrambled_sequences_screen(which_seq = 2)

            for probe_ix in range(10):
                quiz_screen()
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

    session = AppliedLearning(args.subject_id)
    session.run()



if __name__ == "__main__":
    main()
