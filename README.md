# replay_task

This repository contains code for a simple implementation of the second task from
[Liu et al., 2019](https://www.cell.com/cell/fulltext/S0092-8674(19)30640-3).

The code is split into three files: 
* training.py -- Run at the start of the Day 1 session
* structure_learning.py -- Run on Day 1, following the training
* applied_learning.py -- Run on Day 2, in the scanner

training.py teaches participants an "unscrambling" rule by explicitly showing
the rule and then repeatedly quizzing participants on the unscrambled sequence.
structure_learning.py tests whether participants can apply the rule in the same
setting they will encounter in the scanner. applied_learning.py implements the
applied learning task from Liu et al 2019, where participants see brand new
stimuli, then have a rest period, and finally have to answer questions about
the true position and true sequence particular stimuli belong to.


## Running the experiment

A working [PsychoPy](https://www.psychopy.org/) installation is required. We
recommend running inside a conda environment like:

```bash
conda create -n psychopy-env -c conda-forge python=3.8 psychopy pyglet=1.5.27
```

Launch with:

```bash
python -m experiment.training <SUBJECT_ID>
python -m experiment.structure_learning <SUBJECT_ID>
python -m experiment.applied_learning <SUBJECT_ID>
```

where `SUBJECT_ID` is a unique integer identifier for the participant. 
The scrambling rule and visual object randomizations are stored in json
files and automatically reused if the same SUBJECT_ID is entered.
