# Cassette Finger Trainer — Phase 1 Spec

## Project identity

Name: Cassette Finger Trainer  
Target: local terminal app on macOS  
Language: Python 3.11+  
UI: curses-based TUI, standard library first  
Packaging target: zip containing runnable script, README, and agentic build spec

## Core goal

A terminal trainer that helps move from loose fingerstyle into repeatable, disciplined fingerpicking by combining:

- a lesson library
- a play-along tab renderer
- timed highlighting
- a simple exercise generator

## Explicit non-goals for v2

No audio synthesis.  
No microphone listening.  
No web tab import yet.  
No dependency-heavy GUI stack.  
No internet requirement.

## Phase 1 user-facing behavior

### Main screens

#### 1. Lesson Library
Shows all built-in lessons plus generated lessons.

Each row shows:
- lesson number/title
- category
- default bpm
- short goal

Actions:
- open selected lesson
- generate a new lesson
- reload saved generated lessons
- quit

#### 2. Lesson Player
Shows the lesson in either split view or compact view.

Split view on:
- top pane: title, goal, pattern, bpm, progression, instructions
- bottom pane: tab display with beat guide and moving highlight

Split view off:
- mostly tab display
- compact status line only

Actions:
- play/pause
- restart from beginning
- toggle split view
- cycle timing mode
- tempo up/down
- return to library

#### 3. Generator Screen
A small form-like screen to create new drills.

Inputs:
- focus
- difficulty
- bar count
- chord palette
- pattern family
- base tempo

Output:
- generated lesson immediately opened in player
- saved to local generated lesson folder as JSON or plain lesson file

## Phase 1 interaction model

### Keys

Library:
- `j / k` or arrow keys: move selection
- `Enter`: open lesson
- `g`: open generator
- `r`: reload generated lessons
- `q`: quit

Lesson player:
- `space`: play/pause
- `0`: restart
- `v`: toggle split view
- `t`: cycle timing mode
- `- / +`: bpm down/up
- `[` / `]`: previous/next lesson
- `b`: back to library
- `q`: back to library

Generator:
- arrow keys or `j / k`: move fields
- `h / l` or left/right: change value
- `Enter`: generate lesson
- `Esc` or `b`: back

### Timing mode toggles

- Beat mode  
- Subdivision mode  
- Note mode

## Phase 1 rendering spec

### Tab model

Each lesson is stored as structured events, not raw pasted tab text.

Each event includes:
- timeline position
- strings struck together
- fret values for visible tab
- optional beat label
- optional note/comment label

The renderer rebuilds tab lines from structured events into six-string ASCII tab.

### Display format

Bottom pane contains:

- beat guide row
- optional bar separators
- six tab lines:
  - e
  - B
  - G
  - D
  - A
  - E

The currently active event is highlighted with reverse video or standout mode.

## Phase 1 lesson set

Built-in library includes:

1. Thumb Clock  
2. Planted Pinch Drill  
3. Static Chord Pinch Memory  
4. Alternating Bass with One Drone  
5. Alternating Bass with Changing Treble Pairs  
6. Forward and Reverse Roll Control  
7. Top-String Melody over Automatic Bass  
8. Inner-Voice Melody Drill  
9. Syncopated Pinch Exercise  
10. Ring-Through Chord Study  
11. Thumb Accent / Dynamic Control  
12. Angeles Prep Etude  
13. Angeles-Inspired Original Study

## Phase 1 generator spec

### Generator inputs

Focus options:
- thumb stability
- pinch control
- alternating bass
- melody independence
- syncopation
- sustain / ring-through
- Elliott-ish arpeggio study

Difficulty:
- easy
- medium
- hard

Bar count:
- 2
- 4
- 8

Chord palettes:
- open major/minor
- C / G/B / Am / Fmaj7 family
- Elliott-ish color chords
- bass-movement studies

Pattern families:
- bass-only
- pinch
- roll
- melody-over-bass
- syncopated pinch
- ring-through arpeggio

### Generator outputs

For every generated lesson:
- title
- goal
- short instructions
- bpm suggestion
- progression
- structured event list
- tags
- saved file on disk

## Phase 1 file layout

- `finger.trainer.<timestamp>.v2.py`
- `finger.trainer.readme.<timestamp>.v2.md`
- `finger.trainer.agent.spec.<timestamp>.v2.md`
- `generated.lessons/` directory created at runtime

## Phase 2 spec: Advanced Importer & Manual Workarounds

### Goal
Bypass web blocks and handle "format hell" ASCII tabs.

### Features
- **Browser Spoofing:** Rotate headers (User-Agent: Chrome/Safari) to bypass basic 403 blocks.
- **Manual File Import:** Ability to parse `.txt` and `.tab` files directly from disk.
- **"Format Hell" Parser:** A heuristic-based parser that scores lines based on dash (`-`) and bar (`|`) density to identify tab blocks even if labels are missing or non-standard.
- **Future Hook:** Headless browser support (Playwright/Selenium) as a future toggleable option.

## Phase 3 spec: Playback Audio & Advanced Practice

### Goal
Enable audio feedback and iterative practice tools.

### Features
- **Metronome:** Audio count-in and steady pulse.
- **A/B Looping:** Set start and end markers to loop difficult sections.
- **Speed Trainer:** Auto-increment BPM every X loops.
- **Fretboard Visualizer:** Real-time ASCII map of the guitar neck showing active notes.

## Phase 4 spec: microphone listening and simple grading

### Goal

Let the user play along and receive basic feedback.

Recommended first scope:
- timing-only drills
- bass-string accuracy drills
- single-note melody drills
- partial event matching with heuristic feedback

## Phase 5 spec: Robust Application Features

### Goal

Transform `pickme` into a highly attractive, comprehensive tool for guitarists.

Recommended scope:
- **Advanced Practice Modes:** Speed Trainer (auto-accelerating BPM) and Subdivision Drills.
- **Standardized File Format Support:** Parse Guitar Pro files (.gp3, .gp4, .gp5) or MusicXML.
- **MIDI Integration:** MIDI Out to trigger synths/samples, and MIDI In for precise grading from a MIDI guitar.
- **Progress Tracking:** Local SQLite database to track practice time, BPM records, and visualize consistency.
- **TUI Tab Editor:** A dedicated authoring view to manually write, edit, and save fingerpicking patterns.
- **ASCII Fretboard Visualization:** Real-time visual representation of the fretboard alongside the scrolling tab.
