# Agentic Build Spec — Cassette Finger Trainer v2

## Build brief

Create a Python terminal application named “Cassette Finger Trainer” that runs locally on macOS using Python 3.11+ and standard-library-first dependencies. The app must provide a lesson library, a lesson player with real-time tab highlighting, a lesson generator, split-view toggle, and timing-mode toggle. Do not implement audio, microphone input, or web import in v2.

## Constraints

- Prefer a single obvious entrypoint.
- Avoid heavy external dependencies.
- Use `curses` for UI unless there is a compelling reason not to.
- Store built-in lessons in code or in a simple local data file.
- Store generated lessons as JSON.
- Handle small terminal sizes gracefully.
- No internet required for v2.
- Include an original “Angeles-inspired” lesson, not a transcription.

## Required screens

1. Library view  
2. Lesson player view  
3. Generator view  
4. Optional help/footer hints

## Required capabilities

- Browse built-in lessons
- Open lesson
- Play/pause lesson
- Restart playback
- Toggle split view
- Toggle timing mode between beat/subdivision/note
- Adjust bpm
- Generate new lessons from parameterized templates
- Save generated lessons
- Reload generated lessons on app start

## Data model requirement

Represent lessons as structured timed events, not only pasted raw tab text.

Each lesson must include:
- metadata
- instructions
- bpm
- progression
- structured event list

Each event must include enough data to render six-line ASCII tab and highlight the active event during playback.

## Rendering requirement

Render:
- beat guide
- six-string ASCII tab
- active event highlight

The active event must visually stand out in terminal.

## Generator requirement

Support generator parameters:
- focus
- difficulty
- bars
- chord palette
- pattern family
- bpm

Generated lessons must be playable and not random garbage.

## Included content requirement

Ship these built-ins:
- 12 core exercises based on right-hand development
- 1 original Angeles-inspired study

## Testing requirement

Provide:
- a self-test mode or validation mode
- basic checks that lessons serialize/deserialize
- no syntax errors
- no crash on missing generated lesson directory

## Deliverables

- runnable Python entrypoint
- README with run instructions and keybindings
- agentic build spec markdown
- zipped package

## Stretch hooks for later phases

Design internals so later phases can add:
- imported lessons
- audio playback
- mic listening
- grading

without rewriting the whole lesson/event model.
