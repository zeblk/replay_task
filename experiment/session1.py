from psychopy import visual, core, event
from .utils import SESSION1_OBJECTS, get_permutation


SCRAMBLED_REPEATS = 5
OBJECT_DURATION = 1.0
REST_DURATION = 1.0


class Session1:
    def __init__(self, subject_id: str):
        self.subject_id = subject_id
        self.perm = get_permutation(subject_id)
        self.win = visual.Window(color="black", fullscr=False)

    def show_object(self, obj_name: str):
        stim = visual.TextStim(self.win, text=obj_name, color="white", height=0.1)
        stim.draw()
        self.win.flip()
        core.wait(OBJECT_DURATION)
        self.win.flip()
        core.wait(0.3)

    def run(self):
        for rep in range(SCRAMBLED_REPEATS):
            # show scrambled sequence
            for idx in self.perm:
                self.show_object(SESSION1_OBJECTS[idx])
            core.wait(REST_DURATION)
            # show unscrambled sequences
            for obj in SESSION1_OBJECTS[:4]:
                self.show_object(obj)
            for obj in SESSION1_OBJECTS[4:]:
                self.show_object(obj)
            core.wait(REST_DURATION)
        self.win.close()
        core.quit()


def main(subject_id: str):
    session = Session1(subject_id)
    session.run()


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python session1.py SUBJECT_ID")
    else:
        main(sys.argv[1])
