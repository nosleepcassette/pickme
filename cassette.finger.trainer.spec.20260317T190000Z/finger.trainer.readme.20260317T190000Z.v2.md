# Cassette Finger Trainer v2

A local Python TUI for fingerpicking drills, timed tab highlighting, and simple exercise generation.

## Files

- `finger.trainer.20260317T190000Z.v2.py` — main runnable app
- `finger.trainer.spec.20260317T190000Z.v2.md` — phase 1 through 4 spec
- `finger.trainer.agent.spec.20260317T190000Z.v2.md` — compact build brief for another coding agent

## Requirements

- macOS or another Unix-like terminal with Python 3.11+
- a terminal with curses support

## Run

```zsh
python3 finger.trainer.20260317T190000Z.v2.py
```

## Validate without launching curses

```zsh
python3 finger.trainer.20260317T190000Z.v2.py --validate
```

## Controls

### Library
- `j / k` or arrows: move
- `Enter`: open lesson
- `g`: open generator
- `i`: open importer
- `r`: reload generated lessons
- `q`: quit

### Player
- `space`: play/pause
- `0`: restart
- `v`: toggle split view
- `t`: cycle timing mode
- `- / +`: bpm down/up
- `[` / `]`: previous / next lesson
- `b`: back to library

### Generator
- arrows or `j / k`: move field
- `h / l` or left/right: change value
- `Enter`: generate lesson
- `b` or `Esc`: back

## Notes

Generated lessons are written into a local `generated.lessons/` folder next to the script. The app ships with the 12 core drills plus an original Angeles-inspired study.

## Planned later phases

- Phase 2: web tab import and cleanup
- Phase 3: playback audio
- Phase 4: mic listening and heuristic grading
