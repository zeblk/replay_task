from __future__ import annotations

from dataclasses import dataclass, field
from psychopy import core, event, visual

from .trigger import MetaPort

fullscreen = True
actual_meg = False
REST_DURATION = 300 # 300 seconds = 5 minutes

@dataclass
class Rest:
    """
    A rest period after applied learning, to look for replay.
    """

    win: visual.Window = field(init=False)
    meg: MetaPort = field(init=False)

    def __post_init__(self) -> None:
        if fullscreen:
            self.win = visual.Window(color="black", fullscr=True, units="norm", allowGUI=False)
        else:
            self.win = visual.Window(color="black", size=(WIN_WIDTH, WIN_HEIGHT), units="norm")

        # Create MEG trigger object
        self.meg = MetaPort(-1, actual_meg)

        event.globalKeys.clear()
        event.globalKeys.add(key="escape", func=self._exit)

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

    def run(self) -> None:

        visual.TextStim(self.win, text='Press space to begin rest period.', height=0.1, pos=(0, .0)).draw()
        self.win.flip()
        event.waitKeys(keyList=["space"])

        self.win.flip()
        self.meg.write('start_rest') # send trigger
        core.wait(REST_DURATION)
        self.meg.write('end_rest') # send trigger


        visual.TextStim(self.win, text="Press space to exit", height=0.1, pos=(0, 0)).draw()
        self.win.flip()
        event.waitKeys(keyList=["space"])
        self.close()
        core.quit()


def main() -> None:
    """Entry point for running the experiment."""

    session = Rest()

    try:
        session.run()
    finally:
        # Ensure resources are closed even if an exception occurs
        session.close()

if __name__ == "__main__":
    main()
