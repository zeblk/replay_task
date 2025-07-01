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
    TRAINING_OBJECTS,
    get_object_mapping,
    get_pos_and_seq,
    get_scrambled_pos_and_seq,
    get_scrambling_rule,
    ordinal_string,
)

# Paths
HERE = Path(__file__).parent
IMAGES_DIR = HERE / "images"


MESSAGE_DURATION = 1.0
SCRAMBLED_REPEATS = 5
OBJECT_DURATION = 0.1
REST_DURATION = 1.0
N_OBJECTS = 8
ISI = 0.1
ITI = 1.5

true_state_names = ['W', 'X', 'Y', 'Z', 'Wp', 'Xp', 'Yp', 'Zp']
scrambled_positions = [0, 1, 2, 3, 4, 5, 6, 7]

warnings.filterwarnings(
    "ignore",
    message="elementwise comparison failed.*",
    category=FutureWarning,
    module=r"psychopy\.visual\.shape"
)


@dataclass
class Training:
    """
    Teaches participants the unscrambling rule before beginning Structure Learning.
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
        self.object_mapping = get_object_mapping(self.subject_id, 'training')
        self.win = visual.Window(color="black", size=(1024, 768), fullscr=False, units="norm")
        event.globalKeys.clear()
        event.globalKeys.add(key="escape", func=self._exit)

        # open behavioral data file
        os.makedirs('behavior_data', exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_name = f"subject_{self.subject_id}_training_behavior_{timestamp}.csv"
        self.behavior_filename = os.path.join('behavior_data', file_name)
        self.behavior_file = open(self.behavior_filename, "w", newline="")
        self.behavior_writer = csv.writer(self.behavior_file)
        self.behavior_writer.writerow([
            "quiz_type",
            "left_stimulus_true_state",
            "left_stimulus_picture",
            "right_stimulus_true_state",
            "right_stimulus_picture",
            "key_pressed",
            "choice",
            "correctness",
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
        stim.size = size
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
            visual.TextStim(self.win, text='Today\'s goal is to learn a rule that will unscramble two sequences of pictures.', height=0.1, pos=(0,0)).draw()

            return ['right']

        def screen2():
            visual.TextStim(self.win, text='You will see two scrambled sequences like this...', height=0.1, pos=(0,0)).draw()
            
            return ['left','right']

        def screen3():
            scrambled_sequences_screen()
            
            return ['left','right']

        def screen4():
           
            visual.TextStim(self.win, text='Then you will have to answer questions, like: does ' + self.object_mapping['W'][1:] + \
                ' come before or after ' + self.object_mapping['X'][1:] + '?', height=0.1, pos=(0,.6)).draw()
            visual.TextStim(self.win, text='**But the questions will be about the unscrambled order, not the order you saw.**', height=0.1, pos=(0,0)).draw()
            visual.TextStim(self.win, text='So you\'ll have to mentally reorder the sequences to answer these questions.', height=0.1, pos=(0,-.5)).draw()

            return ['left','right']

        def screen5():
            visual.TextStim(self.win, text='**Here is the rule**', height=0.12, pos=(0,.7)).draw()

            name_mapping = {'W': 'A', 'X': 'B', 'Y': 'C', 'Z': 'D', 'Wp': '1', 'Xp': '2', 'Yp': '3', 'Zp': '4'}
            ss_1 = "-".join([name_mapping[self.reverse_state_lookup(i)] for i in range(4)])
            ss_2 = "-".join([name_mapping[self.reverse_state_lookup(i)] for i in range(4,8)])

            visual.TextStim(self.win, text='Scrambled sequence 1: ', height=0.1, pos=(0,.5)).draw()
            visual.TextStim(self.win, text=ss_1, height=0.12, pos=(0,.4)).draw()
            visual.TextStim(self.win, text='Scrambled sequence 2: ', height=0.1, pos=(0,.2)).draw()
            visual.TextStim(self.win, text=ss_2, height=0.12, pos=(0,.1)).draw()

            visual.TextStim(self.win, text='True sequence 1: ', height=0.1, pos=(0,-.1)).draw()
            visual.TextStim(self.win, text='A-B-C-D', height=0.12, pos=(0,-.2)).draw()
            visual.TextStim(self.win, text='True sequence 2: ', height=0.1, pos=(0,-.4)).draw()
            visual.TextStim(self.win, text='1-2-3-4', height=0.12, pos=(0,-.5)).draw()

            return ['left','right']

        def screen6():
            visual.TextStim(self.win, text='Tomorrow, you will apply the same rule to unscramble two *new* sequences of pictures.', height=0.1, pos=(0,.5)).draw()
            visual.TextStim(self.win, text='You earn money by applying today\'s rule to tomorrow\'s pictures.', height=0.1, pos=(0,.05)).draw()
            visual.TextStim(self.win, text='So it\'s really important to *learn the rule* today.', height=0.1, pos=(0,-.35)).draw()

            return ['left', 'space']
        
        def rule_screen(true_state: str):
            name_mapping = {'W': 'A', 'X': 'B', 'Y': 'C', 'Z': 'D', 'Wp': '1', 'Xp': '2', 'Yp': '3', 'Zp': '4'}
            ss_1 = [name_mapping[self.reverse_state_lookup(i)] for i in range(4)]
            ss_2 = [name_mapping[self.reverse_state_lookup(i)] for i in range(4,8)]

            visual.TextStim(self.win, text='Scrambled sequence 1: ', height=0.07, pos=(-.67,.8)).draw()
            for i, s in enumerate(ss_1):
                visual.TextStim(self.win, text=s, height=0.12, pos=(-.32 + i*0.09,.8)).draw()
            for i in range(3):
                visual.TextStim(self.win, text='-', height=0.12, pos=(-.28 + i*0.09,.8)).draw()

            visual.TextStim(self.win, text='Scrambled sequence 2: ', height=0.07, pos=(-.67,.65)).draw()
            for i, s in enumerate(ss_2):
                visual.TextStim(self.win, text=s, height=0.12, pos=(-.32 + i*0.09,.65)).draw()
            for i in range(3):
                visual.TextStim(self.win, text='-', height=0.12, pos=(-.28 + i*0.09,.65)).draw()

            visual.TextStim(self.win, text='True sequence 1: ', height=0.07, pos=(.37,.8)).draw()
            for i, s in enumerate(['A','B','C','D']):
                visual.TextStim(self.win, text=s, height=0.12, pos=(.62 + i*0.09,.8)).draw()
            for i in range(3):
                visual.TextStim(self.win, text='-', height=0.12, pos=(.66 + i*0.09,.8)).draw()

            visual.TextStim(self.win, text='True sequence 2: ', height=0.07, pos=(.37,.65)).draw()
            for i, s in enumerate(['1','2','3','4']):
                visual.TextStim(self.win, text=s, height=0.12, pos=(.62 + i*0.09,.65)).draw()
            for i in range(3):
                visual.TextStim(self.win, text='-', height=0.12, pos=(.66 + i*0.09,.65)).draw()

            visual.TextStim(self.win, text='Let\'s focus on this part of the rule:', height=0.1, pos=(0,.2)).draw()

            pos, seq = get_pos_and_seq(true_state)
            s_pos, s_seq = get_scrambled_pos_and_seq(self.scrambling_rule[true_state])

            # Highlight the scrambled state
            visual.Circle(self.win, size=(.08,.105), 
                pos=(-.32 + (s_pos-1)*0.09, 0.65 + 0.15*int(s_seq==1)), 
                lineColor='red', lineWidth=3, fillColor=None).draw()

            # Highlight the true state
            visual.Circle(self.win, size=(.08,.105), 
                pos=(0.62 + (pos-1)*0.09, 0.65 + 0.15*int(seq==1)), 
                lineColor='red', lineWidth=3, fillColor=None).draw()

            visual.TextStim(self.win, text='The ' + ordinal_string(s_pos) + ' picture in the ' + ordinal_string(s_seq) + \
                            ' scrambled sequence is the ' + ordinal_string(pos) + ' picture of the ' + \
                            ordinal_string(seq)  + ' true sequence.', height=0.1, pos=(0,-.2)).draw()

        def scrambled_sequences_screen():
            for scrambled_position in [0, 1, 2, 3]:
                visual.TextStim(self.win, text='Scrambled sequence 1', height=0.1, pos=(0,0.5)).draw()
                state_name = self.reverse_state_lookup(scrambled_position)
                self.get_object(state_name, size=(0.5,0.5), pos=(0,0)).draw()
                self.win.flip()
                core.wait(OBJECT_DURATION)

            self.win.flip()
            core.wait(ISI)

            for scrambled_position in [4, 5, 6, 7]:
                visual.TextStim(self.win, text='Scrambled sequence 2', height=0.1, pos=(0,0.5)).draw()
                state_name = self.reverse_state_lookup(scrambled_position)
                self.get_object(state_name, size=(0.5,0.5), pos=(0,0)).draw()
                self.win.flip()
                core.wait(OBJECT_DURATION)
            
            self.win.flip()
            core.wait(ISI)

        def seq_quiz_screen(true_state: str):
            picture_name = self.object_mapping[true_state][1:]
            visual.TextStim(self.win, text='Which sequence does', height=0.1, pos=(0,.7)).draw()
            self.get_object(true_state, size=(0.3,0.3), pos=(0,.5)).draw()
            visual.TextStim(self.win, text='belong to?', height=0.1, pos=(0,.3)).draw()

            true_pos, true_seq = get_pos_and_seq(true_state)

            # Draw the two choices
            visual.TextStim(self.win, text='Sequence 1', height=0.1, pos=(-.5,-.45)).draw()
            visual.TextStim(self.win, text='Sequence 2', height=0.1, pos=(.5,-.45)).draw()
            visual.TextStim(self.win, text='(Press left)', height=0.07, pos=(-.5,-.6)).draw()
            visual.TextStim(self.win, text='(Press right)', height=0.07, pos=(.5,-.6)).draw()
            self.win.flip()
            clock = core.Clock()
            key_data = event.waitKeys(keyList=["left", "right", "escape"], timeStamped=clock)
            key, rt = key_data[0]
            chosen_seq = 1 if key == "left" else 2
            correct_bool = ((key == "left") and (true_seq == 1)) or ((key == "right") and (true_seq == 2))
            if correct_bool:
                visual.TextStim(self.win, text="Correct!", height=0.1, pos=(0,0)).draw()
                result = "correct"
            else:
                s_pos, s_seq = get_scrambled_pos_and_seq(self.scrambling_rule[true_state])
                visual.TextStim(self.win, text="Incorrect. Remember:", height=0.1, pos=(0,0.3)).draw()
                visual.TextStim(self.win, text="The " + ordinal_string(s_pos) + " picture of the " + ordinal_string(s_seq) + " scrambled sequence "
                    + "becomes the " + ordinal_string(true_pos) + " picture of the **" + ordinal_string(true_seq)  + " true sequence**.", height=0.1, pos=(0,-.2)).draw()
                result = "incorrect"
            self.behavior_writer.writerow([
                "sequence",
                true_state,
                picture_name,
                "",
                "",
                key,
                'seq'+str(chosen_seq),
                result,
                rt,
            ])
            self.behavior_file.flush()
            return result


        def order_quiz_screen(true_state_1: str, true_state_2: str):
            true_pos_1, true_seq_1 = get_pos_and_seq(true_state_1)
            true_pos_2, true_seq_2 = get_pos_and_seq(true_state_2)
            assert true_seq_1==true_seq_2, 'ERROR: Can only compare order within one true sequence'

            visual.TextStim(self.win, text='Which comes later in the ' + ordinal_string(true_seq_1) + ' true sequence?', 
                            height=0.1, pos=(0,.4)).draw()

            # Draw the two choices
            self.get_object(true_state_1, size=(0.3,0.3), pos=(-.5,-.4)).draw()
            self.get_object(true_state_2, size=(0.3,0.3), pos=(.5,-.4)).draw()
            visual.TextStim(self.win, text='(Press left)', height=0.07, pos=(-.5,-.7)).draw()
            visual.TextStim(self.win, text='(Press right)', height=0.07, pos=(.5,-.7)).draw()
            self.win.flip()
            clock = core.Clock()
            key_data = event.waitKeys(keyList=["left", "right", "escape"], timeStamped=clock)
            key, rt = key_data[0]
            chosen_state = true_state_1 if key == "left" else true_state_2
            chosen_obj = self.object_mapping[chosen_state][1:]
            first_on_left = true_pos_1 < true_pos_2
            correct_bool = ((key == "left") and (not first_on_left)) or ((key == "right") and first_on_left)
            if correct_bool:
                visual.TextStim(self.win, text="Correct!", height=0.1, pos=(0,0)).draw()
                result = "correct"
            else:
                visual.TextStim(self.win, text="Incorrect. Remember:", height=0.1, pos=(0,0.6)).draw()
                s_pos, s_seq = get_scrambled_pos_and_seq(self.scrambling_rule[true_state_1])
                visual.TextStim(self.win, text="The " + ordinal_string(s_pos) + " picture in the " + ordinal_string(s_seq) + 
                    " scrambled sequence becomes the " + ordinal_string(true_pos_1) + 
                    " picture of the " + ordinal_string(true_seq_1)  + " true sequence.", height=0.1, pos=(0,.2)).draw()
                s_pos_2, s_seq_2 = get_scrambled_pos_and_seq(self.scrambling_rule[true_state_2])
                visual.TextStim(self.win, text="The " + ordinal_string(s_pos_2) + " picture in the " + ordinal_string(s_seq_2) + 
                    " scrambled sequence becomes the " + ordinal_string(true_pos_2) + 
                    " picture of the " + ordinal_string(true_seq_2)  + " true sequence.", height=0.1, pos=(0,-.3)).draw()
                result = "incorrect"
            self.behavior_writer.writerow([
                "order",
                true_state_1,
                self.object_mapping[true_state_1][1:],
                true_state_2,
                self.object_mapping[true_state_2][1:],
                key,
                chosen_state,
                result,
                rt,
            ])
            self.behavior_file.flush()
            return result


        ####################### Do the intro

        intro_screens = [screen1, screen2, screen3, screen4, screen5, screen6]
        screen_ix = 0
        done = False
        while not done:
            # Draw the current screen
            available_keys = intro_screens[screen_ix]()
            keys = left_right_msg(available_keys)
            
            if keys[0] == 'left':
                screen_ix -= 1
            elif keys[0] == 'space':
                done = True
            elif keys[0] == 'right':
                screen_ix += 1
            screen_ix = np.maximum(np.minimum(screen_ix, len(intro_screens)-1), 0)

        ####################### Do the training

        # Learning level from 0 (unseen) to 3 (fully learned)
        learning_levels = {state: 0 for state in true_state_names}

        def states_at_level(dict_of_levels, level: int):
            ''' return a list of state names that are currently at a specified level of learning '''
            return [k for k, v in dict_of_levels.items() if v == level]
        def states_above_level(dict_of_levels, level: int):
            ''' return a list of state names that are currently above a specified level of learning '''
            return [k for k, v in dict_of_levels.items() if v > level]

        # Keep training while any states are below max proficiency level
        current_lowest_level = min(learning_levels.values())
        while current_lowest_level < 3:

            # train a state from the least-learned tier
            print('current_lowest_level: ' + str(current_lowest_level))
            print('states_at_level(current_lowest_level): ' + str(states_at_level(learning_levels, current_lowest_level)))

            true_state = random.choice(states_at_level(learning_levels, current_lowest_level))
            pos, seq = get_pos_and_seq(true_state)

            rule_screen(true_state=true_state)
            left_right_msg(['space'])
            scrambled_sequences_screen()
            quiz_result = seq_quiz_screen(true_state=true_state)
            left_right_msg(['space'])

            # If there's another state above level-0 in this sequence, then also do a 'which comes first' quiz.
            quiz_result_2 = 'correct'
            true_state_2 = None
            states_in_same_seq = [s for s in states_above_level(learning_levels, 0) if (seq==get_pos_and_seq(s)[1] and s != true_state)]
            if states_in_same_seq:
                true_state_2 = random.choice(states_in_same_seq)
                quiz_result_2 = order_quiz_screen(true_state_1=true_state,true_state_2=true_state_2)
                left_right_msg(['space'])

            if quiz_result == 'correct' and quiz_result_2 == 'correct':
                learning_levels[true_state] += 1
            else:
                # Don't allow learning level to go back below 1. So we can use any seen state as a reference for order quizzes.
                if learning_levels[true_state] > 1:
                    learning_levels[true_state] -= 1
                if true_state_2 and learning_levels[true_state_2] > 1:
                    learning_levels[true_state_2] -= 1

            current_lowest_level = min(learning_levels.values())
            print('learning_levels: ' + str(learning_levels))

        visual.TextStim(self.win, text="All done. Great job.", height=0.1, pos=(0,0.0)).draw()
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

    session = Training(args.subject_id)
    session.run()



if __name__ == "__main__":
    main()
