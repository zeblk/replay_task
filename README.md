# replay_task

This repository contains code for a simple implementation of the second task from
[Liu et al., 2019](https://www.cell.com/cell/fulltext/S0092-8674(19)30640-3).

The experiment is split into two sessions that should be run on separate days.
Session 1 teaches participants an "unscrambling" rule by repeatedly showing
scrambled sequences of objects followed by the same objects in their correct
order. In session 2 participants see eight new objects scrambled using the same
rule and then rest so replay can be measured.

## Running the experiment

A working [PsychoPy](https://www.psychopy.org/) installation is required. We
recommend running inside a conda environment like:

```bash
conda create -n psychopy-env -c conda-forge python=3.8 psychopy pyglet=1.5.27
```

Launch the experiment with:

```bash
python -m experiment.experiment <SUBJECT_ID>
```

where `SUBJECT_ID` is a unique integer identifier for the participant. 
The scrambling rule and visual object randomizations are stored in json
files and automatically reused if the same SUBJECT_ID is entered.
