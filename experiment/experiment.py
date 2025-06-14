from psychopy import visual, core, event
from PIL import Image
import argparse
import numpy as np
from .utils import get_scrambling_rule, get_object_mapping
import os


MESSAGE_DURATION = 1.0
SCRAMBLED_REPEATS = 5
OBJECT_DURATION = 0.5
REST_DURATION = 1.0
N_OBJECTS = 8
ISI = 0.5
ITI = 1.5


class Experiment:
    def __init__(self, subject_id: str):
        self.subject_id = subject_id
        self.scrambling_rule = get_scrambling_rule(subject_id)
        self.object_mapping = get_object_mapping(subject_id)
        self.win = visual.Window(color="black", size=(1024,768), fullscr=False, units='norm')
        event.globalKeys.clear()
        event.globalKeys.add(key="escape", func=self._exit)
        self.end_experiment = False

        # pre-load images
        self.object_stims = {}
        for letter in self.object_mapping:
            obj_name = self.object_mapping[letter]
            img_path = os.path.join(os.path.dirname(__file__), "images", f"{obj_name}.png")
            self.object_stims[letter] = visual.ImageStim(self.win, image=img_path)

    def _exit(self):
        self.end_experiment = True
        print('Esc detected: ending experiment...')

    def get_object(self, obj_letter: str, size: tuple=(0.5, 0.5), pos: tuple=(0,0)):
        """Display an image corresponding to the specified object letter (W, X, Y, Z, Wp, Xp, Yp, Zp)."""
        # Specify the image size in 'norm' units. (1,1) would fill a quarter of the screen.
        stim = self.object_stims[obj_letter]
        stim.size = size
        stim.pos = pos
        return stim


    def run(self):
        
        def left_right_msg(which_ones=('L','R')):
            """ Draw left/right navigation instructions for participants """
            if 'L' in which_ones:
                visual.TextStim(self.win, text='←left', color='white', height=0.05, pos=(-.9,-.9)).draw()
            if 'R' in which_ones:
                visual.TextStim(self.win, text='right→', color='white', height=0.05, pos=(.9,-.9)).draw()

        def screen1():
            visual.TextStim(self.win, text='Today\'s goal is to learn a rule that will unscramble two sequences of pictures.', height=0.1, pos=(0,0)).draw()
            left_right_msg('R')
            self.win.flip()
        def screen2():
            visual.TextStim(self.win, text='Tomorrow, you will apply this same rule to unscramble two *new* sequences of pictures.', height=0.1, pos=(0,.5)).draw()
            visual.TextStim(self.win, text='You earn money by applying today\'s rule to tomorrow\'s pictures.', height=0.1, pos=(0,.05)).draw()
            visual.TextStim(self.win, text='So it\'s really important to learn the rule today.', height=0.1, pos=(0,-.35)).draw()
            left_right_msg()
            self.win.flip()
        def screen3():
            visual.TextStim(self.win, text='What you will see, both today and tomorrow, is two sequences of pictures in scrambled order, like this:', height=0.1, pos=(0,.4)).draw()
            self.get_object(self.scrambling_rule['W'], size=(0.2,0.2), pos=(-0.85,0)).draw()
            self.get_object(self.scrambling_rule['X'], size=(0.2,0.2), pos=(-0.65,0)).draw()
            self.get_object(self.scrambling_rule['Y'], size=(0.2,0.2), pos=(-0.45,0)).draw()
            self.get_object(self.scrambling_rule['Z'], size=(0.2,0.2), pos=(-0.25,0)).draw()
            self.get_object(self.scrambling_rule['Wp'], size=(0.2,0.2), pos=(0.25,0)).draw()
            self.get_object(self.scrambling_rule['Xp'], size=(0.2,0.2), pos=(0.45,0)).draw()
            self.get_object(self.scrambling_rule['Yp'], size=(0.2,0.2), pos=(0.65,0)).draw()
            self.get_object(self.scrambling_rule['Zp'], size=(0.2,0.2), pos=(0.85,0)).draw()
            visual.TextStim(self.win, text='(Note that the pictures will appear *one at a time* on the screen.)', height=0.1, pos=(0,-0.4)).draw()
            left_right_msg()
            self.win.flip()
        def screen4():
            visual.TextStim(self.win, text='You have to unscramble them into the two *true* sequences, like this:', height=0.1, pos=(0,.35)).draw()
            self.get_object('W', size=(0.2,0.2), pos=(-0.85,0.)).draw()
            self.get_object('X', size=(0.2,0.2), pos=(-0.65,0)).draw()
            self.get_object('Y', size=(0.2,0.2), pos=(-0.45,0)).draw()
            self.get_object('Z', size=(0.2,0.2), pos=(-0.25,0)).draw()
            self.get_object('Wp', size=(0.2,0.2), pos=(0.25,0)).draw()
            self.get_object('Xp', size=(0.2,0.2), pos=(0.45,0)).draw()
            self.get_object('Yp', size=(0.2,0.2), pos=(0.65,0)).draw()
            self.get_object('Zp', size=(0.2,0.2), pos=(0.85,0)).draw()
            left_right_msg()
            self.win.flip()
        def screen5():
            visual.TextStim(self.win, text='Remember: tomorrow, the rule for reordering the pictures will be the same, but the pictures themselves will be completely new.', height=0.1, pos=(0,0)).draw()
            left_right_msg()
            self.win.flip()
        def screen6():
            visual.TextStim(self.win, text='Here\'s an example of how this will look.', height=0.1, pos=(0,0)).draw()
            self.win.flip()
            core.wait(MESSAGE_DURATION)
            for letter in ['W', 'X', 'Y', 'Z']:
                self.get_object(self.scrambling_rule[letter], size=(0.5,0.5), pos=(0,0)).draw()
                self.win.flip()
                core.wait(0.5)
            self.win.flip()
            core.wait(1.0)
            for letter in ['Wp', 'Xp', 'Yp', 'Zp']:
                self.get_object(self.scrambling_rule[letter], size=(0.5,0.5), pos=(0,0)).draw()
                self.win.flip()
                core.wait(0.5)
            visual.TextStim(self.win, text='(Don\'t worry, it will go slower so you have time to take it in.)', height=0.1, pos=(0,0)).draw()
            left_right_msg()
            self.win.flip()


        screens_list = [screen1, screen2, screen3, screen4, screen5, screen6]

        screen_ix = 0
        done = False
        while not done and not self.end_experiment:

            # Draw the current screen
            screens_list[screen_ix]()

            # Wait for key input
            keys = event.waitKeys(keyList=['left', 'right', 'escape'])
            print(f"You pressed: {keys[0]}")
            if keys[0] == 'left':
                screen_ix -= 1
            elif keys[0] == 'right':
                screen_ix += 1
            screen_ix = np.maximum(np.minimum(screen_ix, len(screens_list)-1), 0)


        for trial in range(SCRAMBLED_REPEATS):
            if self.end_experiment:
                break

            # show scrambled sequence
            stim = visual.TextStim(self.win, text="Scrambled sequence...", color="white", height=0.1)
            stim.draw()
            self.win.flip()
            core.wait(MESSAGE_DURATION)
            
            for stim_ix_perm in self.perm:
                if self.end_experiment:
                    break
                self.show_object(SESSION1_OBJECTS[stim_ix_perm])

            core.wait(ITI)

            # show unscrambled sequences
            if not self.end_experiment:
                stim = visual.TextStim(self.win, text="Unscrambled sequence...", color="white", height=0.1)
                stim.draw()
                self.win.flip()
                core.wait(MESSAGE_DURATION)

            for stim_ix in range(N_OBJECTS):
                if self.end_experiment:
                    break
                self.show_object(SESSION1_OBJECTS[stim_ix])

            core.wait(ITI)
        self.win.close()
        core.quit()



parser = argparse.ArgumentParser(description="Task 2 from Liu et al (2019) cell")
parser.add_argument("subject_id", help="Unique subject identifier")


def main(subject_id: str):
    args = parser.parse_args()
    session = Experiment(args.subject_id)
    session.run()



if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python experiment.py SUBJECT_ID")
    else:
        main(sys.argv[1])
