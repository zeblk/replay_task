# replay_task

This repository contains code for a simple implementation of the second task from
[Liu et al., 2019](https://www.cell.com/cell/fulltext/S0092-8674(19)30640-3).

The experiment is split into two sessions that should be run on separate days.
Session 1 teaches participants an "unscrambling" rule by repeatedly showing
scrambled sequences of objects followed by the same objects in their correct
order. In session 2 participants see eight new objects scrambled using the same
rule and then rest so replay can be measured.

## Running the experiment

A working [PsychoPy](https://www.psychopy.org/) installation is required.
Install dependencies with:

```bash
pip install psychopy
```

Launch the experiment with:

```bash
python -m experiment.experiment <SESSION> <SUBJECT_ID>
```

where `SESSION` is `1` or `2` and `SUBJECT_ID` is a unique identifier for the
participant. The permutation used to scramble the sequences is stored in
`perm_<SUBJECT_ID>.json` and is automatically reused across sessions.
