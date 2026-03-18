# pickme - Fingerpicking Guitar Trainer

A terminal-based guitar fingerpicking practice application for macOS.

## Version History

### v2.4 (current)
- Multiple audio backend support: pygame, sounddevice, simpleaudio, afplay
- Select audio backend via --audio-backend flag
- Left hand finger display on fretboard (which finger to fret)
- Right hand finger display under tab (which finger to pluck)
- Finger mapping: fret 0=T, 1-3=I, 4-6=M, 7-9=R, 10+=P
- Plucking fingers: e=B(4), G=M(2), D/A/E=T(0)
- Metronome disabled by default
- Fixed case sensitivity in finger display
- Case-insensitive string lookup for notes

### v2.3
- Initial pygame.mixer implementation (audio issues)
- Basic fretboard display

### v2.0-2.2
- Development iterations with Gemini AI

### v1.0
- Initial concept

## Features

### Current Features
- **Lesson Library**: 13 built-in lessons
- **Lesson Generator**: Create custom drills
- **Tab Importer**: Import guitar tabs
- **Playback**: Variable speed with loop markers
- **Audio**: Multiple backend support
- **Finger Tracking**: Left/right hand display

### Planned Features
- [ ] Save/load user preferences
- [ ] Metronome customization
- [ ] Progress tracking
- [ ] Export lessons to PDF
- [ ] MIDI input support
- [ ] Recording feature

## Installation

```bash
pip install pygame
pip install sounddevice numpy
pip install simpleaudio
python3 pickme.py
```

## Usage

```bash
python3 pickme.py --audio-backend pygame
python3 pickme.py --audio-backend sounddevice
python3 pickme.py --audio-backend simpleaudio
python3 pickme.py --audio-backend afplay
```

## Audio Backends

| Backend | Dependencies |
|---------|-------------|
| auto | any |
| pygame | pygame |
| sounddevice | sounddevice, numpy |
| simpleaudio | simpleaudio |
| afplay | none |

## License

MIT
