from psychopy import visual, core, event
from PIL import Image
from .utils import get_scrambling_rule, get_object_mapping
import os


SCRAMBLED_REPEATS = 5
OBJECT_DURATION = 0.5
ISI = 0.5
REST_PERIOD = 20.0
ITI = 1.0
MESSAGE_DURATION = 1.0

class Session2:
    def __init__(self, subject_id: str):
        self.subject_id = subject_id
        self.perm = get_permutation(subject_id)
        self.win = visual.Window(color="black", size=(1024,768), fullscr=False, units='norm')
        event.globalKeys.clear()
        event.globalKeys.add(key="escape", func=self._exit)
        self.end_experiment = False

    def _exit(self):
        self.end_experiment = True
        print('Esc detected: ending experiment...')

    def show_object(self, obj_name: str):
        """Display an image corresponding to the given object name."""
        img_path = os.path.join(os.path.dirname(__file__), "images", f"{obj_name}.png")
        if os.path.exists(img_path):
            # Specify the image size in 'norm' units. (1,1) would fill a quarter of the screen.
            stim = visual.ImageStim(self.win, image=img_path, size=(0.5, 0.5))
        else:
            stim = visual.TextStim(self.win, text=obj_name, color="white", height=0.1)
        stim.draw()
        self.win.flip()
        core.wait(OBJECT_DURATION)
        self.win.flip()
        core.wait(ISI)

    def run(self):
        
        for trial in range(SCRAMBLED_REPEATS):
            if self.end_experiment:
                break

            stim = visual.TextStim(self.win, text="Scrambled sequence...", color="white", height=0.1)
            stim.draw()
            self.win.flip()
            core.wait(MESSAGE_DURATION)

            # show scrambled sequence using this subject's permutation
            for stim_ix_perm in self.perm:
                if self.end_experiment:
                    break

                self.show_object(SESSION2_OBJECTS[stim_ix_perm])

            core.wait(ITI)

        # rest period for replay measurement
        if not self.end_experiment:
            msg = visual.TextStim(self.win, text="Rest", color="white")
            msg.draw()
            self.win.flip()
            core.wait(REST_PERIOD)

        self.win.close()
        core.quit()


def main(subject_id: str):
    session = Session2(subject_id)
    session.run()


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python session2.py SUBJECT_ID")
    else:
        main(sys.argv[1])
