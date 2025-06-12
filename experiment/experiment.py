import argparse
from .session1 import main as run_session1
from .session2 import main as run_session2


parser = argparse.ArgumentParser(description="Two-session unscrambling experiment")
parser.add_argument("session", choices=["1", "2"], help="Session number to run")
parser.add_argument("subject_id", help="Unique subject identifier")


def main():
    args = parser.parse_args()
    if args.session == "1":
        run_session1(args.subject_id)
    else:
        run_session2(args.subject_id)


if __name__ == "__main__":
    main()
