from __future__ import annotations

import argparse
import numpy as np
import csv
import os
import random
import warnings
from dataclasses import dataclass, field
from datetime import datetime
from itertools import combinations
from pathlib import Path
from typing import Dict

from psychopy import core, event, visual

from .utils import (
    get_object_mapping,
    get_pos_and_seq,
    get_scrambled_pos_and_seq,
    get_scrambling_rule,
    ordinal_string,
)

fullscreen = True
GLOBAL_DEBUG = False # Do not use this when running subjects. It makes all quiz question answers magically correct.

# Paths & constants
ROOT_DIR = Path(__file__).resolve().parent
IMAGES_DIR = ROOT_DIR / "images"
BEHAVIOR_DIR = ROOT_DIR.parent / "behavior_data"
WIN_WIDTH = 800
WIN_HEIGHT = 600


if GLOBAL_DEBUG:
    # For debugging
    MESSAGE_DURATION = 0.1
    SCRAMBLED_REPEATS = 5
    OBJECT_DURATION = 0.1
    REST_DURATION = .1
    N_OBJECTS = 8
    ISI = .1
    ITI = .1
else:
    # For participants
    MESSAGE_DURATION = 1.0
    SCRAMBLED_REPEATS = 5
    OBJECT_DURATION = 0.9
    REST_DURATION = 1.0
    N_OBJECTS = 8
    ISI = 1.0
    ITI = 1.5

true_state_names = ['W', 'X', 'Y', 'Z', 'Wp', 'Xp', 'Yp', 'Zp']
scrambled_positions = [0, 1, 2, 3, 4, 5, 6, 7]
state_map = {'W': 1, 'X': 2, 'Y': 3, 'Z': 4, 'Wp': 5, 'Xp': 6, 'Yp': 7, 'Zp': 8}
nseq = len(scrambled_positions)

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
    behavior_file: any = field(init=False)
    behavior_writer: csv.writer = field(init=False)
    scrambling_rule: Dict[str, int] = field(init=False)
    inv_scrambling_rule: Dict[int, str] = field(init=False)
    object_mapping: Dict[str, str] = field(init=False)
    object_stims: Dict[str, visual.ImageStim] = field(init=False)
    rng: random.Random = field(init=False)

    def __post_init__(self) -> None:
        # Load rule & mapping for TRAINING phase
        self.scrambling_rule = get_scrambling_rule(self.subject_id)
        self.inv_scrambling_rule = {v: k for k, v in self.scrambling_rule.items()}
        self.object_mapping = get_object_mapping(self.subject_id, 'training')

        if fullscreen:
            self.win = visual.Window(color="black", fullscr=True, units="norm", allowGUI=False)
        else:
            self.win = visual.Window(color="black", size=(WIN_WIDTH, WIN_HEIGHT), units="norm")

        event.globalKeys.clear()
        event.globalKeys.add(key="escape", func=self._exit)

        # Behaviour file
        BEHAVIOR_DIR.mkdir(exist_ok=True, parents=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.behavior_file = open(
            BEHAVIOR_DIR / f"subject_{self.subject_id}_training_behavior_{ts}.csv",
            "w",
            newline=""
        )
        self.behavior_writer = csv.writer(self.behavior_file)
        self.behavior_writer.writerow([
            "subject_id",
            "quiz_type",
            "left_stimulus_picture",
            "left_stimulus_true_state",
            "left_stim_number",
            "left_stim_seq",
            "right_stimulus_picture",
            "right_stimulus_true_state",
            "right_stim_number",
            "right_stim_seq",
            "key_pressed",
            "choice",
            "choice_stim_number",
            "choice_stim_seq",
            "correct",
            "reaction_time"
        ])

        # Deterministic RNG per participant
        self.rng = random.Random(self.subject_id)
        self.preload_images()

    def _exit(self):
        print("Esc detected: ending experiment...")
        self.close()
        core.quit()
        os._exit(0)

    def preload_images(self) -> None:
        """Preload images for the current mapping into PsychoPy stimuli cache."""
        self.object_stims = {}
        for letter, obj_name in self.object_mapping.items():
            img_path = IMAGES_DIR / f"{obj_name}.png"
            self.object_stims[letter] = visual.ImageStim(self.win, image=str(img_path))

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

    def get_object(self, true_state: str, size=(0.5, 0.5), pos=(0, 0)) -> visual.ImageStim:
        """Display an image corresponding to the specified object letter (W, X, Y, Z, Wp, Xp, Yp, Zp)."""
        stim = self.object_stims[true_state]
        orig_w, orig_h = stim.size
        s_f = min(size[0] / orig_w, size[1] / orig_h)
        stim.size = (orig_w * s_f, orig_h * s_f)
        stim.pos = pos
        return stim

    def reverse_state_lookup(self, scrambled_index: int) -> str:
        """Given scrambled position index 0..7, return the true-state letter (W..Z, Wp..Zp)."""
        return self.inv_scrambling_rule[scrambled_index]

    def run(self) -> None:
        """
        Main training flow - simplified incorrect feedback:
        1. Shows only "Incorrect" (no explanation)
        2. Shows rule_screen
        3. Shows full scrambled sequences again
        4. Retries the same question
        """

        def left_right_msg(available_keys: list):
            """ Draw left/right/space navigation instructions for participants """
            if 'left' in available_keys:
                visual.TextStim(self.win, text='< left', color='white', height=0.05, pos=(-.9, -.9)).draw()
            if 'space' in available_keys:
                visual.TextStim(self.win, text='Press space to continue', color='white', height=0.05, pos=(0, -.9)).draw()
            if 'right' in available_keys:
                visual.TextStim(self.win, text='right >', color='white', height=0.05, pos=(.9, -.9)).draw()
            self.win.flip()
            keys = event.waitKeys(keyList=available_keys + ['escape'])
            return keys

        # INTRO SCREENS (unchanged)
        def screen1():
            visual.TextStim(self.win, text="Today's goal is to learn a rule that will unscramble two sequences of pictures.", height=0.1, pos=(0, 0)).draw()
            return ['right']

        def screen2():
            visual.TextStim(self.win, text='You will see two scrambled sequences like this...', height=0.1, pos=(0, 0)).draw()
            return ['left', 'right']

        def screen3():
            scrambled_sequences_screen()
            return ['left', 'right']

        def screen4():
            visual.TextStim(self.win, text='Then you will have to answer questions, like: does ' + self.object_mapping['W'][1:] +
                            ' come before or after ' + self.object_mapping['X'][1:] + '?', height=0.1, pos=(0, .6)).draw()
            visual.TextStim(self.win, text='But the questions will be about the unscrambled order, not the order you saw.', height=0.1, pos=(0, 0), bold=True).draw()
            visual.TextStim(self.win, text="So you'll have to mentally reorder the sequences to answer these questions.", height=0.1, pos=(0, -.5)).draw()
            return ['left', 'right']

        def screen5():
            visual.TextStim(self.win, text='Here is the rule. We will help you learn it today.', height=0.12, pos=(0, .7), bold=True).draw()

            name_mapping = {'W': 'A', 'X': 'B', 'Y': 'C', 'Z': 'D', 'Wp': '1', 'Xp': '2', 'Yp': '3', 'Zp': '4'}
            ss_1 = "-".join([name_mapping[self.reverse_state_lookup(i)] for i in range(4)])
            ss_2 = "-".join([name_mapping[self.reverse_state_lookup(i)] for i in range(4, 8)])

            visual.TextStim(self.win, text='Scrambled sequence 1: ', height=0.1, pos=(0, .4)).draw()
            visual.TextStim(self.win, text=ss_1, height=0.12, pos=(0, .3)).draw()
            visual.TextStim(self.win, text='Scrambled sequence 2: ', height=0.1, pos=(0, .2)).draw()
            visual.TextStim(self.win, text=ss_2, height=0.12, pos=(0, .1)).draw()

            visual.TextStim(self.win, text='True sequence 1: ', height=0.1, pos=(0, -.2)).draw()
            visual.TextStim(self.win, text='A-B-C-D', height=0.12, pos=(0, -.3)).draw()
            visual.TextStim(self.win, text='True sequence 2: ', height=0.1, pos=(0, -.4)).draw()
            visual.TextStim(self.win, text='1-2-3-4', height=0.12, pos=(0, -.5)).draw()
            return ['left', 'right']

        def screen6():
            visual.TextStim(self.win, text='Tomorrow, you will apply the same rule to unscramble new sequences of pictures.', height=0.1, pos=(0, .5)).draw()
            visual.TextStim(self.win, text="You will earn points by applying today's rule to tomorrow's pictures.", height=0.1, pos=(0, .05)).draw()
            visual.TextStim(self.win, text="So it's really important to learn the rule today.", height=0.1, pos=(0, -.35)).draw()
            return ['left', 'space']

        # Rules
        def rule_screen(true_state: str):
            """Focused rule explanation screen for a single state."""
            name_mapping = {'W': 'A', 'X': 'B', 'Y': 'C', 'Z': 'D', 'Wp': '1', 'Xp': '2', 'Yp': '3', 'Zp': '4'}
            ss_1 = [name_mapping[self.reverse_state_lookup(i)] for i in range(4)]
            ss_2 = [name_mapping[self.reverse_state_lookup(i)] for i in range(4, 8)]

            visual.TextStim(self.win, text='Scrambled sequence 1: ', height=0.07, pos=(-.67, .8)).draw()
            for i, s in enumerate(ss_1):
                visual.TextStim(self.win, text=s, height=0.12, pos=(-.32 + i * 0.09, .8)).draw()
            for i in range(3):
                visual.TextStim(self.win, text='-', height=0.12, pos=(-.28 + i * 0.09, .8)).draw()

            visual.TextStim(self.win, text='Scrambled sequence 2: ', height=0.07, pos=(-.67, .65)).draw()
            for i, s in enumerate(ss_2):
                visual.TextStim(self.win, text=s, height=0.12, pos=(-.32 + i * 0.09, .65)).draw()
            for i in range(3):
                visual.TextStim(self.win, text='-', height=0.12, pos=(-.28 + i * 0.09, .65)).draw()

            visual.TextStim(self.win, text='True sequence 1: ', height=0.07, pos=(.37, .8)).draw()
            for i, s in enumerate(['A', 'B', 'C', 'D']):
                visual.TextStim(self.win, text=s, height=0.12, pos=(.62 + i * 0.09, .8)).draw()
            for i in range(3):
                visual.TextStim(self.win, text='-', height=0.12, pos=(.66 + i * 0.09, .8)).draw()

            visual.TextStim(self.win, text='True sequence 2: ', height=0.07, pos=(.37, .65)).draw()
            for i, s in enumerate(['1', '2', '3', '4']):
                visual.TextStim(self.win, text=s, height=0.12, pos=(.62 + i * 0.09, .65)).draw()
            for i in range(3):
                visual.TextStim(self.win, text='-', height=0.12, pos=(.66 + i * 0.09, .65)).draw()

            visual.TextStim(self.win, text="Here's one piece of the rule:", height=0.1, pos=(0, .2)).draw()

            pos, seq = get_pos_and_seq(true_state)
            s_pos, s_seq = get_scrambled_pos_and_seq(self.scrambling_rule[true_state])

            # Highlight the scrambled state
            visual.Circle(
                self.win, size=(.08, .105),
                pos=(-.32 + (s_pos - 1) * 0.09, 0.65 + 0.15 * int(s_seq == 1)),
                lineColor='red', lineWidth=3, fillColor=None
            ).draw()

            # Highlight the true state
            visual.Circle(
                self.win, size=(.08, .105),
                pos=(0.62 + (pos - 1) * 0.09, 0.65 + 0.15 * int(seq == 1)),
                lineColor='red', lineWidth=3, fillColor=None
            ).draw()

            visual.TextStim(
                self.win,
                text='The ' + ordinal_string(s_pos) + ' picture in the ' + ordinal_string(s_seq) +
                     ' scrambled sequence is the ' + ordinal_string(pos) + ' picture of the ' +
                     ordinal_string(seq) + ' true sequence.',
                height=0.1, pos=(0, -.2)
            ).draw()

        def scrambled_sequences_screen():
            """
            Show scrambled sequences with proper positioning.
            """
            # Clear the screen first
            self.win.flip()
            
            # Show sequence 1 title, then wait briefly
            visual.TextStim(self.win, text='Scrambled sequence 1', height=0.12, pos=(0,0)).draw()
            self.win.flip()
            core.wait(MESSAGE_DURATION)  # Brief pause to read title
            
            # Sequence 1: positions [0..3] with fixation before each stimulus
            for scrambled_position in [0, 1, 2, 3]:
                # Fixation cross (no sequence title)
                visual.TextStim(self.win, text='+', color='white', height=0.3, pos=(0,0)).draw()
                self.win.flip()
                core.wait(ISI)

                # Show stimulus
                state_name = self.reverse_state_lookup(scrambled_position)
                self.get_object(state_name, size=(0.5, 0.5), pos=(0,0)).draw()
                self.win.flip()
                core.wait(OBJECT_DURATION)
            
            # Clear and prepare for sequence 2
            self.win.flip()
            core.wait(ISI)

            # Show sequence 2 title, then wait briefly  
            visual.TextStim(self.win, text='Scrambled sequence 2', height=0.12, pos=(0,0)).draw()
            self.win.flip()
            core.wait(MESSAGE_DURATION)  # Brief pause to read title

            # Sequence 2: positions [4..7] with fixation before each stimulus
            for scrambled_position in [4, 5, 6, 7]:
                # Fixation cross (no sequence title)
                visual.TextStim(self.win, text='+', color='white', height=0.3, pos=(0,0)).draw()
                self.win.flip()
                core.wait(ISI)

                # Show stimulus
                state_name = self.reverse_state_lookup(scrambled_position)
                self.get_object(state_name, size=(0.5, 0.5), pos=(0,0)).draw()
                self.win.flip()
                core.wait(OBJECT_DURATION)

            # Final clear
            self.win.flip()
            core.wait(ISI)

        def seq_quiz_screen_base(true_state: str):
            """
            Base sequence quiz function (called by retry wrapper).
            SIMPLIFIED: Shows only "Incorrect!" without explanation.
            """
            picture_name = self.object_mapping[true_state][1:]
            stim_number = state_map[true_state]
            stim_seq = 1 if true_state in ['W', 'X', 'Y', 'Z'] else 2

            visual.TextStim(self.win, text='Which sequence does', height=0.1, pos=(0, .7)).draw()
            self.get_object(true_state, size=(0.3, 0.3), pos=(0, .5)).draw()
            visual.TextStim(self.win, text='belong to?', height=0.1, pos=(0, .3)).draw()

            true_pos, true_seq = get_pos_and_seq(true_state)

            # Draw the two choices
            visual.TextStim(self.win, text='Sequence 1', height=0.1, pos=(-.5, -.45)).draw()
            visual.TextStim(self.win, text='Sequence 2', height=0.1, pos=(.5, -.45)).draw()
            visual.TextStim(self.win, text='(Press left)', height=0.07, pos=(-.5, -.6)).draw()
            visual.TextStim(self.win, text='(Press right)', height=0.07, pos=(.5, -.6)).draw()
            
            self.win.flip()
            clock = core.Clock()
            key_data = event.waitKeys(keyList=["left", "right", "escape"], timeStamped=clock)
            key, rt = key_data[0]
            
            if key == "escape":
                return "escape"

            chosen_seq = 1 if key == "left" else 2
            correct_bool = ((key == "left") and (true_seq == 1)) or ((key == "right") and (true_seq == 2))

            if GLOBAL_DEBUG:
                correct_bool = True
            
            if correct_bool:
                visual.TextStim(self.win, text="Correct!", height=0.1, pos=(0, 0)).draw()
                self.win.flip()
                core.wait(MESSAGE_DURATION)
                result = "correct"
            else:
                # SIMPLIFIED: Just show "Incorrect!" without the explanation
                visual.TextStim(self.win, text="Incorrect!", height=0.1, pos=(0, 0)).draw()
                self.win.flip()
                core.wait(MESSAGE_DURATION)
                result = "incorrect"

            choice_stim_seq = chosen_seq

            # Save to CSV
            try:
                self.behavior_writer.writerow([
                    self.subject_id,
                    "sequence",
                    picture_name,
                    true_state,
                    stim_number,
                    stim_seq,
                    "",        # right_stimulus_picture
                    "",        # right_stimulus_true_state
                    "",        # right_stim_number
                    "",        # right_stim_seq
                    key,
                    chosen_seq,
                    stim_number,
                    choice_stim_seq,        
                    result,
                    rt,
                ])
                self.behavior_file.flush()
                os.fsync(self.behavior_file.fileno())
            except Exception as e:
                print(f"Error writing to CSV: {e}")
                
            return result

        def order_quiz_screen_base(true_state_1: str, true_state_2: str):
            """
            Base order quiz function (called by retry wrapper).
            SIMPLIFIED: Shows only "Incorrect!" without explanation.
            """
            true_pos_1, true_seq_1 = get_pos_and_seq(true_state_1)
            true_pos_2, true_seq_2 = get_pos_and_seq(true_state_2)
            assert true_seq_1 == true_seq_2, 'ERROR: Can only compare order within one true sequence'

            visual.TextStim(self.win, text='Which comes later in the ' + ordinal_string(true_seq_1) + ' true sequence?',
                            height=0.1, pos=(0, .4)).draw()

            # Draw the two choices
            self.get_object(true_state_1, size=(0.3, 0.3), pos=(-.5, -.4)).draw()
            self.get_object(true_state_2, size=(0.3, 0.3), pos=(.5, -.4)).draw()
            visual.TextStim(self.win, text='(Press left)', height=0.07, pos=(-.5, -.7)).draw()
            visual.TextStim(self.win, text='(Press right)', height=0.07, pos=(.5, -.7)).draw()
            
            self.win.flip()
            clock = core.Clock()
            key_data = event.waitKeys(keyList=["left", "right", "escape"], timeStamped=clock)
            key, rt = key_data[0]
            
            if key == "escape":
                return "escape"

            chosen_state = true_state_1 if key == "left" else true_state_2
            chosen_obj = self.object_mapping[chosen_state][1:]
            chosen_state_num = state_map[chosen_state]
            first_on_left = true_pos_1 < true_pos_2
            correct_bool = ((key == "left") and (not first_on_left)) or ((key == "right") and first_on_left)
            
            if GLOBAL_DEBUG:
                correct_bool = True

            if correct_bool:
                visual.TextStim(self.win, text="Correct!", height=0.1, pos=(0, 0)).draw()
                self.win.flip()
                core.wait(MESSAGE_DURATION)
                result = "correct"
            else:
                # SIMPLIFIED: Just show "Incorrect!" without the explanation
                visual.TextStim(self.win, text="Incorrect!", height=0.1, pos=(0, 0)).draw()
                self.win.flip()
                core.wait(MESSAGE_DURATION)
                result = "incorrect"

            l_stim_number = state_map[true_state_1]
            l_stim_seq = 1 if true_state_1 in ['W', 'X', 'Y', 'Z'] else 2
            r_stim_number = state_map[true_state_2]
            r_stim_seq = 1 if true_state_2 in ['W', 'X', 'Y', 'Z'] else 2
            choice_stim_seq = 1 if chosen_state in ['W', 'X', 'Y', 'Z'] else 2

            # Save to CSV
            try:
                self.behavior_writer.writerow([
                    self.subject_id,
                    "order",
                    self.object_mapping[true_state_1][1:],
                    true_state_1,
                    l_stim_number,
                    l_stim_seq,
                    self.object_mapping[true_state_2][1:],
                    true_state_2,
                    r_stim_number,
                    r_stim_seq,
                    key,
                    chosen_state,
                    chosen_state_num,
                    choice_stim_seq,          
                    result,
                    rt,
                ])
                self.behavior_file.flush()
                os.fsync(self.behavior_file.fileno())
            except Exception as e:
                print(f"Error writing to CSV: {e}")
                
            return result

        # SIMPLIFIED retry wrappers
        def seq_quiz_screen(true_state: str):
            """
            Retry wrapper for sequence quiz.
            If incorrect: shows rule_screen, then scrambled_sequences_screen, then retries.
            """
            max_retries = 5
            retry_count = 0
            
            while retry_count < max_retries:

                result = seq_quiz_screen_base(true_state=true_state)

                print(f'retry_count: {retry_count}')
                print(f'result: {result}')

                if result in ("correct", "escape"):
                    return result
                    
                # If incorrect: show rule, then full sequences, then retry
                rule_screen(true_state=true_state)
                left_right_msg(['space'])
                scrambled_sequences_screen()
                retry_count += 1
            
            print(f"Warning: Maximum retries exceeded for sequence quiz on state {true_state}")
            return result

        def order_quiz_screen(true_state_1: str, true_state_2: str):
            """
            Retry wrapper for order quiz.
            If incorrect: shows rule_screen for the first state, then scrambled_sequences_screen, then retries.
            """
            max_retries = 5
            retry_count = 0
            
            while retry_count < max_retries:

                result = order_quiz_screen_base(true_state_1=true_state_1, true_state_2=true_state_2)

                print(f'retry_count: {retry_count}')
                print(f'result: {result}')

                if result in ("correct", "escape"):
                    return result
                    
                # If incorrect: show rule for first state, then full sequences, then retry
                rule_screen(true_state=true_state_1)
                left_right_msg(['space'])
                scrambled_sequences_screen()
                retry_count += 1
            
            print(f"Warning: Maximum retries exceeded for order quiz on states {true_state_1}, {true_state_2}")
            return result

        def show_full_rule_screen():
            """Show the full rule with letters/numbers (no images)."""
            visual.TextStim(self.win, text="Now, we will quiz you about any part of this rule.", height=0.1, pos=(0, .7)).draw()

            name_mapping = {'W': 'A', 'X': 'B', 'Y': 'C', 'Z': 'D', 'Wp': '1', 'Xp': '2', 'Yp': '3', 'Zp': '4'}
            
            # Scrambled sequences
            ss_1 = "-".join([name_mapping[self.reverse_state_lookup(i)] for i in range(4)])
            ss_2 = "-".join([name_mapping[self.reverse_state_lookup(i)] for i in range(4, 8)])
            
            visual.TextStim(self.win, text='Scrambled sequence 1: ', height=0.1, pos=(0, .5)).draw()
            visual.TextStim(self.win, text=ss_1, height=0.12, pos=(0, .4)).draw()
            visual.TextStim(self.win, text='Scrambled sequence 2: ', height=0.1, pos=(0, .2)).draw()
            visual.TextStim(self.win, text=ss_2, height=0.12, pos=(0, .1)).draw()
            
            # True sequences
            visual.TextStim(self.win, text='True sequence 1: ', height=0.1, pos=(0, -.1)).draw()
            visual.TextStim(self.win, text='A-B-C-D', height=0.12, pos=(0, -.2)).draw()
            visual.TextStim(self.win, text='True sequence 2: ', height=0.1, pos=(0, -.4)).draw()
            visual.TextStim(self.win, text='1-2-3-4', height=0.12, pos=(0, -.5)).draw()
            
            visual.TextStim(self.win, text="Press space to continue", height=0.05, pos=(0, -.9)).draw()


        # ================= Intro navigator =================
        
        intro_screens = [screen1, screen2, screen3, screen4, screen5, screen6]
        screen_ix, done_intro = 0, False
        while not done_intro:
            available_keys = intro_screens[screen_ix]()
            keys = left_right_msg(available_keys)
            k = keys[0]
            if k == 'left':
                screen_ix = max(screen_ix - 1, 0)
            elif k == 'right':
                screen_ix = min(screen_ix + 1, len(intro_screens) - 1)
            elif k == 'space':
                done_intro = True
            elif k == 'escape':
                self.close()
                core.quit()
            screen_ix = np.maximum(np.minimum(screen_ix, len(intro_screens)-1), 0)
        
        # Initialize learning levels to zero
        learning_levels = {state: 0 for state in true_state_names}
        
        def states_at_level(dict_of_levels, level: int):
            return [k for k, v in dict_of_levels.items() if v == level]

        def states_above_level(dict_of_levels, level: int):
            return [k for k, v in dict_of_levels.items() if v > level]

        def random_state_from_same_seq(state_name):
            pos, seq = get_pos_and_seq(state_name)
            states_in_same_seq = [s for s in true_state_names if
              (seq == get_pos_and_seq(s)[1] and s != state_name)]
            return self.rng.choice(states_in_same_seq)

        def random_same_seq_pair(strong_states):
            """
            Return a random pair (s1, s2) from strong_states that belong to the same
            sequence per get_pos_and_seq(s)[1]. Return None if no such pair exists.
            """
            pairs = [
                (a, b)
                for a, b in combinations(strong_states, 2)
                if get_pos_and_seq(a)[1] == get_pos_and_seq(b)[1]
            ]
            return random.choice(pairs) if pairs else None

        def permute_and_show_seqs():
            ''' Assumes quiz_state_1 and quiz_state_2 come from the same true sequence
            '''
            visual.TextStim(self.win, text='Now we\'ll show a *new sequence* of pictures.', height=0.1, pos=(0, .3)).draw()
            visual.TextStim(self.win, text='The rule always stays the same.', height=0.1, pos=(0, 0)).draw()
            visual.TextStim(self.win, text="(Press space to continue)", height=0.07, pos=(0, -.7)).draw()
            self.win.flip()
            event.waitKeys(keyList=["space"])

            # Re-permute the visual objects and show the scrambled sequence
            self.object_mapping = get_object_mapping(self.subject_id, 'training', force_new=True)
            self.preload_images()
            scrambled_sequences_screen()

        def do_quizzes(learning_levels, quiz_state_1, quiz_state_2):
            ''' Assumes quiz_state_1 and quiz_state_2 come from the same true sequence
            '''

            # Do a sequence-membership quiz
            quiz_result_1 = seq_quiz_screen(true_state=quiz_state_1)
            if quiz_result_1 == "escape":
                self.close()
                core.quit()
                return
            left_right_msg(['space'])

            # Update learning levels based on performance
            if quiz_result_1 == 'correct':
                learning_levels[quiz_state_1] += 1
            else:
                # Do not allow learning level to drop below 0
                if learning_levels[quiz_state_1] > 0:
                    learning_levels[quiz_state_1] -= 1

                # If there was an error, we will refresh this part of the rule
                rule_screen(true_state=quiz_state_1)
                left_right_msg(['space'])

            # Also do an order quiz
            quiz_result_2 = order_quiz_screen(true_state_1=quiz_state_1, true_state_2=quiz_state_2)
            if quiz_result_2 == "escape":
                self.close()
                core.quit()
                return
            left_right_msg(['space'])

            # Update learning levels based on performance
            if quiz_result_2 == 'correct':
                learning_levels[quiz_state_1] += 1
                learning_levels[quiz_state_2] += 1
            else:
                learning_levels[quiz_state_1] = 0
                learning_levels[quiz_state_2] = 0

                # If there was an error, we will refresh these two parts of the rule
                rule_screen(true_state=quiz_state_1)
                left_right_msg(['space'])

                rule_screen(true_state=quiz_state_2)
                left_right_msg(['space'])

        # ================= Train pieces of rule =================

        # Loop through until all parts of the rule have gained proficiency
        current_lowest_level = min(learning_levels.values())
        while current_lowest_level < 3:

            # Train two states, where at least one comes from the least-learned tier
            print(f"learning_levels: {learning_levels}")
            print(f"current_lowest_level: {current_lowest_level}")
            states_at_lowest_level = states_at_level(learning_levels, current_lowest_level)
            print(f"states_at_lowest_level: {states_at_lowest_level}")
            train_state_1 = self.rng.choice(states_at_lowest_level)
            rule_screen(true_state=train_state_1)
            left_right_msg(['space'])

            train_state_2 = random_state_from_same_seq(train_state_1)
            rule_screen(true_state=train_state_2)
            left_right_msg(['space'])

            # Get participants up to level 3 proficiency on these two parts of the rule
            while learning_levels[train_state_1] < 3 or learning_levels[train_state_2] < 3:
                print(f"train_state_1: {train_state_1}")
                print(f"train_state_2: {train_state_2}")
                print(f"learning_levels: {learning_levels}")

                # Quiz on train states (randomize which is no1 and which is no2)
                quiz_state_1, quiz_state_2 = random.sample([train_state_1, train_state_2], k=2)
                permute_and_show_seqs()
                do_quizzes(learning_levels, quiz_state_1, quiz_state_2)

                # Also quiz on any two other well-learned states, if there are any two belonging to the same sequence
                strong_states = set(states_above_level(learning_levels, 1))
                strong_states_diff = list(strong_states - set([train_state_1, train_state_2]))
                strong_pair = random_same_seq_pair(strong_states_diff)
                if strong_pair:
                    quiz_state_1, quiz_state_2 = strong_pair
                    do_quizzes(learning_levels, quiz_state_1, quiz_state_2)

            # Update learning levels
            current_lowest_level = min(learning_levels.values())

        # ================= Open quizzes on all states, under a stable mapping =================

        visual.TextStim(self.win, text="Now we will do many quiz questions under stable sequences!", height=0.1, pos=(0, 0.0)).draw()
        visual.TextStim(self.win, text="Press space to continue.", height=0.08, pos=(0, -0.5)).draw()
        self.win.flip()
        event.waitKeys(keyList=["space"])
        permute_and_show_seqs()

        for _ in range(40):
            quiz_state_1 = self.rng.choice(true_state_names)
            quiz_state_2 = random_state_from_same_seq(quiz_state_1)

            do_quizzes(learning_levels, quiz_state_1, quiz_state_2)


        # ================= End-of-session screen =================

        visual.TextStim(self.win, text="All done. Great job.", height=0.1, pos=(0, 0.0)).draw()
        visual.TextStim(self.win, text="Press space to exit", height=0.07, pos=(0, -0.5)).draw()
        self.win.flip()
        event.waitKeys(keyList=["space"])
        self.close()
        core.quit()


def main() -> None:
    """Entry point for running the experiment."""
    parser = argparse.ArgumentParser(description="Task 2 from Liu et al (2019) cell")
    parser.add_argument("subject_id", type=int, help="Unique subject identifier")
    args = parser.parse_args()

    session = Training(args.subject_id)
    try:
        session.run()
    finally:
        # Ensure resources are closed even if an exception occurs
        session.close()

if __name__ == "__main__":
    main()
