# Changelog

## [2.4] - 2025-03-17

### Added
- Multiple audio backend support (pygame, sounddevice, simpleaudio, afplay)
- --audio-backend command line argument for selecting audio backend
- Left hand finger display on fretboard (which finger to fret)
- Right hand finger display under tab (which finger to pluck)
- Finger mapping: fret 0=T, 1-3=I, 4-6=M, 7-9=R, 10+=P for fretting
- Plucking fingers: e=B(4), G=M(2), D/A/E=T(0)
- Rename field now starts empty

### Changed
- Metronome disabled by default
- Fixed case sensitivity bug in finger display (uppercase E/D/A vs lowercase)
- Improved tone generation with cleaner sine waves

### Fixed
- Added missing run() method to TrainerApp
- Fixed early return after pygame install
- Audio crackling issues (multiple backend attempts)
- Removed pygame dependency for basic functionality

## [2.3] - 2025-03-17

### Added
- Initial pygame.mixer implementation
- Basic fretboard display

### Known Issues
- Audio crackling on some systems

## [2.0-2.2] - 2025-03-17

### Added
- Development iterations with Gemini AI
- Initial lesson system
- Tab import functionality

## [1.0] - 2025-03-17

### Added
- Initial concept
