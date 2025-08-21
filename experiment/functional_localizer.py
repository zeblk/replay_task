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

from psychopy import core, event, visual

from .trigger import MetaPort
from .utils import SESSION2_OBJECTS

actual_meg = True
fullscreen = True

# Paths and constants
HERE = Path(__file__).parent
IMAGES_DIR = HERE / "images"
WIN_WIDTH = 900
WIN_HEIGHT = 700

IMAGE_MIN = 0.6
IMAGE_MAX = 0.8
TEXT_DURATION = 3.0
FEEDBACK_DURATION = 1.0
ITI_MIN = 1.0
ITI_MAX = 1.5

CORRECT_KEY = "1"
INCORRECT_KEY = "2"

warnings.filterwarnings(
    "ignore",
    message="elementwise comparison failed.*",
    category=FutureWarning,
    module=r"psychopy\.visual\.shape",
)


@dataclass
class FunctionalLocalizer:
    """Functional localizer task presenting images with name verification."""

    subject_id: int
    win: visual.Window = field(init=False)
    behavior_file: object = field(init=False)
    behavior_writer: csv.writer = field(init=False)
    object_stims: Dict[str, visual.ImageStim] = field(init=False)
    rng: random.Random = field(init=False)
    meg: MetaPort = field(init=False)
    
    def __post_init__(self) -> None:
        if fullscreen:
            self.win = visual.Window(color="black", fullscr=True, units="norm", allowGUI=False)
        else:
            self.win = visual.Window(color="black", size=(WIN_WIDTH, WIN_HEIGHT), units="norm")

        event.globalKeys.clear()
        event.globalKeys.add(key="escape", func=self._exit)

        # Create MEG trigger object
        self.meg = MetaPort(self.subject_id, actual_meg)

        os.makedirs("behavior_data", exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"subject_{self.subject_id}_functional_localizer_behavior_{timestamp}.csv"
        self.behavior_file = open(Path("behavior_data") / filename, "w", newline="")
        self.behavior_writer = csv.writer(self.behavior_file)
        self.behavior_writer.writerow(
            [
                "subject_id",
                "trial_number",
                "image_name",
                "text_name",
                "is_match",
                "key_pressed",
                "is_correct",
                "reaction_time",
            ]
        )

        self.rng = random.Random(self.subject_id)
        self.preload_images()

    def _exit(self) -> None:
        print("Esc detected: ending experiment...")
        self.close()
        core.quit()
        os._exit(0)

    def preload_images(self) -> None:
        self.object_stims = {}
        for obj_name in SESSION2_OBJECTS:
            img_path = IMAGES_DIR / f"{obj_name}.png"
            self.object_stims[obj_name] = visual.ImageStim(self.win, image=str(img_path))

    def close(self) -> None:
        self.meg.close() # close the trigger system
        try:
            self.win.close()
            visual.Window._closeAllWindows()
        except Exception:
            pass
        try:
            self.behavior_file.close()
        except Exception:
            pass

    def get_object(self, obj_name: str, size=(0.5, 0.5), pos=(0, 0)) -> visual.ImageStim:
        stim = self.object_stims[obj_name]
        orig_w, orig_h = stim.size
        s_f = min(size[0] / orig_w, size[1] / orig_h)
        stim.size = (orig_w * s_f, orig_h * s_f)
        stim.pos = pos
        return stim

    def build_trials(self) -> list[str]:
        trials = []
        for _ in range(30):
            perm = self.rng.sample(SESSION2_OBJECTS, len(SESSION2_OBJECTS))
            trials.extend(perm)
        return trials

    def draw_photodiode_square(self) -> None:
        w, h = self.win.size
        s = 50  # square size in pixels
        visual.Rect(self.win, width=s, height=s, units='pix', fillColor='white',
                    pos=(w/2 - s/2, -h/2 + s/2)).draw()

    def run(self) -> None:
        trial_order = self.build_trials()
        match_flags = [True] * 120 + [False] * 120
        self.rng.shuffle(match_flags)

        # Draw instructions

        visual.TextStim(self.win, text="A picture will appear, followed by a word. " + \
            "If the word *matches* the picture, press " + CORRECT_KEY + ". " + \
            "Otherwise, press " + INCORRECT_KEY + ". ", color="white", height=0.1, pos=(0, .3)).draw()
        visual.TextStim(self.win, text="(get ready to begin)", color="white", height=0.08, pos=(0, -.6)).draw()
        self.win.flip()
        keys = event.waitKeys(keyList=["space"])

        # Functional Localizer main trial loop

        for trial_num, obj_name in enumerate(trial_order, start=1):
            event.clearEvents()
            is_match = match_flags[trial_num - 1]
            image_duration = self.rng.uniform(IMAGE_MIN, IMAGE_MAX)

            # Determine text name
            if is_match:
                text_name = obj_name
            else:
                others = [o for o in SESSION2_OBJECTS if o != obj_name]
                text_name = self.rng.choice(others)

            # Show image
            self.get_object(obj_name).draw()
            self.draw_photodiode_square()
            self.meg.write(obj_name) # send trigger
            self.win.flip()
            core.wait(image_duration)

            # 50 ms between image and text, to give a break in the photodiode square
            self.win.flip()
            core.wait(0.05)

            # Show name of object
            text_label = text_name[1:].capitalize()
            visual.TextStim(self.win, text=text_label, color="white", height=0.1, pos=(0, 0)).draw()
            self.draw_photodiode_square()
            self.meg.write(text_label) # send trigger
            self.win.flip()

            # Get keypress from user
            resp_clock = core.Clock()
            keys = event.waitKeys(maxWait=TEXT_DURATION, keyList=[CORRECT_KEY, INCORRECT_KEY], timeStamped=resp_clock)

            if keys:
                key, rt = keys[0]
                self.meg.write(key + '_press') # send trigger

                correct = (key == CORRECT_KEY and is_match) or (key == INCORRECT_KEY and not is_match)
                feedback = "Correct" if correct else "Incorrect"
                self.behavior_writer.writerow(
                    [self.subject_id, trial_num, obj_name, text_name, is_match, key, correct, rt]
                )
            else:
                feedback = "please respond faster"
                self.behavior_writer.writerow(
                    [self.subject_id, trial_num, obj_name, text_name, is_match, "", "", ""]
                )

            visual.TextStim(self.win, text=feedback, color="white", height=0.1, pos=(0, 0)).draw()
            self.win.flip()
            self.meg.write('feedback_message') # send trigger
            core.wait(FEEDBACK_DURATION)

            iti = self.rng.uniform(ITI_MIN, ITI_MAX)
            visual.TextStim(self.win, text="+", color="white", height=0.2, pos=(0, 0)).draw()
            self.meg.write('fixation') # send trigger
            self.win.flip()
            core.wait(iti)

        self.close()


def main():
    parser = argparse.ArgumentParser(description="Run the functional localizer task.")
    parser.add_argument("subject_id", type=int, help="Unique subject identifier")
    args = parser.parse_args()
    task = FunctionalLocalizer(subject_id=args.subject_id)
    task.run()


if __name__ == "__main__":
    main()
