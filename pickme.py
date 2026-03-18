#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import curses
import json
import math
import os
import random
import re
import shutil
import struct
import textwrap
import time
import urllib.request
import urllib.error
import wave
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Sequence

try:
    import pygame
except ImportError:
    pygame = None

try:
    import sounddevice as sd
except ImportError:
    sd = None

try:
    import numpy as np
except ImportError:
    np = None

try:
    import simpleaudio as sa
except ImportError:
    sa = None

APP_NAME = "pickme"
VERSION = "2.4"
STRING_ORDER = ["e", "B", "G", "D", "A", "E"]
STRING_TO_FINGER = {"e": "3", "B": "2", "G": "1", "D": "0", "A": "0", "E": "0"}
FINGER_NAMES = {0: "T", 1: "1", 2: "2", 3: "3", 4: "4"}
STRING_TO_RIGHT_FINGER = {"e": "4", "B": "3", "G": "2", "D": "1", "A": "0", "E": "0"}
FINGER_LOOKUP = {k.lower(): v for k, v in STRING_TO_RIGHT_FINGER.items()}
CELL_WIDTH = 3
TIMING_MODES = ["beat", "subdivision", "note"]
SOUND_DIR = Path.home() / ".pickme_sounds"

FOCUS_OPTIONS = [
    "thumb stability",
    "pinch control",
    "alternating bass",
    "melody independence",
    "syncopation",
    "sustain / ring-through",
    "Elliott-ish arpeggio study",
]
DIFFICULTY_OPTIONS = ["easy", "medium", "hard"]
BAR_OPTIONS = [2, 4, 8]
PALETTE_OPTIONS = [
    "open major/minor",
    "C / G-B / Am / Fmaj7 family",
    "Elliott-ish color chords",
    "bass-movement studies",
]
PATTERN_OPTIONS = [
    "bass-only",
    "pinch",
    "roll",
    "melody-over-bass",
    "syncopated pinch",
    "ring-through arpeggio",
]
BPM_OPTIONS = [50, 60, 72, 84, 96, 108, 120]

CHORDS = {
    "OPEN": {
        "shape": {"e": 0, "B": 0, "G": 0, "D": 0, "A": 0, "E": 0},
        "bass_pair": ["E", "D"],
    },
    "C": {
        "shape": {"e": 0, "B": 1, "G": 0, "D": 2, "A": 3, "E": None},
        "bass_pair": ["A", "D"],
    },
    "Cmaj7": {
        "shape": {"e": 0, "B": 0, "G": 0, "D": 2, "A": 3, "E": None},
        "bass_pair": ["A", "D"],
    },
    "Am": {
        "shape": {"e": 0, "B": 1, "G": 2, "D": 2, "A": 0, "E": None},
        "bass_pair": ["A", "D"],
    },
    "Am7": {
        "shape": {"e": 0, "B": 1, "G": 0, "D": 2, "A": 0, "E": None},
        "bass_pair": ["A", "D"],
    },
    "G/B": {
        "shape": {"e": 3, "B": 3, "G": 0, "D": 0, "A": 2, "E": None},
        "bass_pair": ["A", "D"],
    },
    "Fmaj7": {
        "shape": {"e": 0, "B": 1, "G": 2, "D": 3, "A": None, "E": None},
        "bass_pair": ["D", "G"],
    },
    "Em": {
        "shape": {"e": 0, "B": 0, "G": 0, "D": 2, "A": 2, "E": 0},
        "bass_pair": ["E", "D"],
    },
    "Em7": {
        "shape": {"e": 0, "B": 3, "G": 0, "D": 2, "A": 2, "E": 0},
        "bass_pair": ["E", "D"],
    },
    "Dsus2": {
        "shape": {"e": 0, "B": 3, "G": 2, "D": 0, "A": None, "E": None},
        "bass_pair": ["D", "G"],
    },
    "Aadd9": {
        "shape": {"e": 0, "B": 0, "G": 6, "D": 7, "A": 0, "E": None},
        "bass_pair": ["A", "D"],
    },
}

PALETTES = {
    "open major/minor": ["C", "Am", "G/B", "Fmaj7"],
    "C / G-B / Am / Fmaj7 family": ["C", "G/B", "Am", "Fmaj7"],
    "Elliott-ish color chords": ["Cmaj7", "G/B", "Am7", "Fmaj7"],
    "bass-movement studies": ["C", "Cmaj7", "Am", "Am7"],
}

PATTERN_TEMPLATES = {
    "bass-only": [["B1"], [], ["B2"], [], ["B1"], [], ["B2"], []],
    "pinch": [
        ["B1", "T1"],
        ["T3"],
        ["B2", "T2"],
        ["T1"],
        ["B1", "T1", "T2"],
        ["T3"],
        ["B2"],
        ["T2"],
    ],
    "roll": [["B1"], ["T3"], ["T1"], ["T2"], ["T1"], ["T3"], ["B2"], ["T3"]],
    "melody-over-bass": [
        ["B1"],
        ["T2"],
        ["B2"],
        ["T2"],
        ["B1"],
        ["T1"],
        ["B2"],
        ["T2"],
    ],
    "syncopated pinch": [
        ["B1"],
        ["T1", "T2"],
        ["B2"],
        [],
        ["B1"],
        ["T3", "T2"],
        ["B2"],
        ["T1"],
    ],
    "ring-through arpeggio": [
        ["B1", "T1"],
        ["T3"],
        ["T2"],
        ["B2"],
        ["T1", "T2"],
        ["T3"],
        ["B1"],
        ["T2"],
    ],
}


@dataclass
class Event:
    step: int
    notes: Dict[str, str]
    label: str = ""


@dataclass
class Lesson:
    lesson_id: str
    title: str
    category: str
    goal: str
    instructions: str
    bpm: int
    progression: List[str]
    pattern_name: str
    bars: int
    steps_per_bar: int
    events: List[Event]
    tags: List[str] = field(default_factory=list)
    generated: bool = False
    source: Optional[str] = None

    def to_json(self) -> str:
        return json.dumps(asdict(self), indent=2)

    @classmethod
    def from_dict(cls, payload: dict) -> "Lesson":
        events = [Event(**evt) for evt in payload.get("events", [])]
        if "source_path" in payload:
            payload["source"] = payload.pop("source_path")
        payload["events"] = events
        return cls(**payload)


def script_dir() -> Path:
    return Path(__file__).resolve().parent


def generated_dir() -> Path:
    path = script_dir() / "generated.lessons"
    path.mkdir(parents=True, exist_ok=True)
    return path


def resolve_symbol(chord_name: str, symbol: str) -> Optional[str]:
    if symbol in STRING_ORDER:
        return symbol
    chord = CHORDS.get(chord_name)
    if not chord:
        return None
    bass_pair = chord["bass_pair"]
    mapping = {
        "B1": bass_pair[0],
        "B2": bass_pair[1],
        "T1": "B",
        "T2": "e",
        "T3": "G",
        "MID": "D",
    }
    return mapping.get(symbol)


def token_to_notes(chord_name: str, token) -> Dict[str, str]:
    if token is None:
        return {}
    if isinstance(token, dict):
        out = {}
        for string_name, fret in token.items():
            if string_name in STRING_ORDER and fret is not None:
                out[string_name] = str(fret)
        return out

    out: Dict[str, str] = {}
    items = token if isinstance(token, (list, tuple)) else [token]
    chord_shape = CHORDS.get(chord_name, {}).get("shape", {})
    for raw in items:
        string_name = resolve_symbol(chord_name, raw)
        if not string_name:
            continue
        fret = chord_shape.get(string_name)
        if fret is not None:
            out[string_name] = str(fret)
    return out


def make_events_from_progression(
    progression: Sequence[str],
    pattern: Sequence,
    steps_per_bar: int = 8,
    labels: Optional[Sequence[str]] = None,
) -> List[Event]:
    events: List[Event] = []
    for bar_index, chord_name in enumerate(progression):
        for local_step in range(steps_per_bar):
            global_step = bar_index * steps_per_bar + local_step
            token = pattern[local_step % len(pattern)]
            label = labels[local_step] if labels and local_step < len(labels) else ""
            events.append(
                Event(
                    step=global_step,
                    notes=token_to_notes(chord_name, token),
                    label=label,
                )
            )
    return events


def add_open_event_pattern(
    pattern: Sequence[Dict[str, str]], bars: int, title_stub: str = ""
) -> List[Event]:
    events: List[Event] = []
    for bar_index in range(bars):
        for local_step, token in enumerate(pattern):
            step = bar_index * len(pattern) + local_step
            events.append(Event(step=step, notes=token, label=title_stub))
    return events


def cycle_progression(seq: Sequence[str], bars: int) -> List[str]:
    out = []
    if not seq:
        return out
    for idx in range(bars):
        out.append(seq[idx % len(seq)])
    return out


def lesson(
    lesson_id: str,
    title: str,
    category: str,
    goal: str,
    instructions: str,
    bpm: int,
    progression: Sequence[str],
    pattern_name: str,
    events: List[Event],
    bars: int,
    steps_per_bar: int = 8,
    tags: Optional[List[str]] = None,
    generated: bool = False,
    source: Optional[str] = None,
) -> Lesson:
    return Lesson(
        lesson_id=lesson_id,
        title=title,
        category=category,
        goal=goal,
        instructions=instructions,
        bpm=bpm,
        progression=list(progression),
        pattern_name=pattern_name,
        bars=bars,
        steps_per_bar=steps_per_bar,
        events=events,
        tags=tags or [],
        generated=generated,
        source=source,
    )


def build_builtin_lessons() -> List[Lesson]:
    lessons: List[Lesson] = []

    thumb_pattern = [
        {"E": "0"},
        {"D": "0"},
        {"A": "0"},
        {"D": "0"},
        {"E": "0"},
        {"D": "0"},
        {"A": "0"},
        {"D": "0"},
    ]
    lessons.append(
        lesson(
            "01-thumb-clock",
            "01. Thumb Clock",
            "thumb stability",
            "Make the thumb automatic and even.",
            "Play with the thumb only. Keep the hand quiet and the bass pulse steady.",
            60,
            ["OPEN"],
            "thumb clock",
            add_open_event_pattern(thumb_pattern, bars=2),
            bars=2,
            tags=["foundation", "thumb"],
        )
    )

    pinch_pattern = [
        ["G", "B"],
        ["B", "e"],
        ["G", "e"],
        ["G", "B", "e"],
        ["G", "B"],
        ["B", "e"],
        ["G", "e"],
        ["G", "B", "e"],
    ]
    lessons.append(
        lesson(
            "02-planted-pinch",
            "02. Planted Pinch Drill",
            "pinch control",
            "Get comfortable striking multiple strings together.",
            "Plant the fingers before plucking. Release cleanly instead of grabbing from the air.",
            56,
            ["C", "C"],
            "pinch",
            make_events_from_progression(["C", "C"], pinch_pattern),
            bars=2,
            tags=["pinch", "simultaneous"],
        )
    )

    static_pattern = [
        ["B1", "T3"],
        ["B1", "T1"],
        ["B1", "T2"],
        ["B1", "T1", "T2"],
        ["B1", "T3"],
        ["B1", "T1"],
        ["B1", "T2"],
        ["B1", "T1", "T2"],
    ]
    prog = ["C", "Am", "G/B", "Fmaj7"]
    lessons.append(
        lesson(
            "03-static-chord-pinch-memory",
            "03. Static Chord Pinch Memory",
            "pinch control",
            "Build right-hand muscle memory inside real chord shapes.",
            "Hold each chord cleanly and map the right hand to the harmony. The pinches should feel deliberate, not guessed.",
            60,
            prog,
            "static chord pinches",
            make_events_from_progression(prog, static_pattern),
            bars=4,
            tags=["pinch", "chords"],
        )
    )

    drone_pattern = [["B1"], ["T1"], ["B2"], ["T1"], ["B1"], ["T1"], ["B2"], ["T1"]]
    prog = ["C", "G/B", "Am", "Fmaj7"]
    lessons.append(
        lesson(
            "04-alternating-bass-one-drone",
            "04. Alternating Bass with One Drone",
            "alternating bass",
            "Keep the bass steady while one finger repeats independently.",
            "The thumb is the floor. Let the repeated treble note sit on top without disturbing the bass motion.",
            66,
            prog,
            "alternating bass + drone",
            make_events_from_progression(prog, drone_pattern),
            bars=4,
            tags=["independence", "bass"],
        )
    )

    changing_pairs = [
        ["B1", "T1"],
        ["T3"],
        ["B2", "T2"],
        ["T1"],
        ["B1", "T3"],
        ["T2"],
        ["B2", "T1"],
        ["T3"],
    ]
    lessons.append(
        lesson(
            "05-alternating-bass-changing-treble-pairs",
            "05. Alternating Bass with Changing Treble Pairs",
            "alternating bass",
            "Combine alternating bass with shifting treble targets.",
            "Do not rush the pair changes. The bass should stay boringly stable while the fingers do the interesting part.",
            68,
            prog,
            "bass + changing treble pairs",
            make_events_from_progression(prog, changing_pairs),
            bars=4,
            tags=["independence", "pairs"],
        )
    )

    roll_pattern = [["B1"], ["T3"], ["T1"], ["T2"], ["T1"], ["T3"], ["B2"], ["T3"]]
    lessons.append(
        lesson(
            "06-forward-reverse-roll-control",
            "06. Forward and Reverse Roll Control",
            "roll control",
            "Make the fingers move in a controlled sequence instead of randomly.",
            "Focus on evenness. The hand should feel like it knows the route before you ask it to go faster.",
            70,
            prog,
            "forward/reverse roll",
            make_events_from_progression(prog, roll_pattern),
            bars=4,
            tags=["roll", "sequence"],
        )
    )

    melody_pattern = [
        ["B1"],
        {"e": "0"},
        ["B2"],
        {"e": "3"},
        ["B1"],
        {"e": "1"},
        ["B2"],
        {"e": "0"},
    ]
    lessons.append(
        lesson(
            "07-top-string-melody-over-bass",
            "07. Top-String Melody over Automatic Bass",
            "melody independence",
            "Carry a top-string line while the thumb keeps time.",
            "The melody has to sing without collapsing the bass pulse. Let the thumb stay relaxed and mechanical.",
            64,
            ["Am", "Am", "C", "C"],
            "melody over bass",
            make_events_from_progression(["Am", "Am", "C", "C"], melody_pattern),
            bars=4,
            tags=["melody", "thumb"],
        )
    )

    inner_prog = ["C", "Cmaj7", "Am", "Am7"]
    inner_pattern = [
        ["B1", "T1"],
        ["T3"],
        ["B2"],
        ["T1"],
        ["B1", "T1"],
        ["T3"],
        ["B2"],
        ["T1"],
    ]
    lessons.append(
        lesson(
            "08-inner-voice-melody-drill",
            "08. Inner-Voice Melody Drill",
            "voice leading",
            "Control harmony changes that happen inside the chord, not only on the top string.",
            "Listen for the moving inner note. The exercise works only if you actually hear the subtle change.",
            60,
            inner_prog,
            "inner voice study",
            make_events_from_progression(inner_prog, inner_pattern),
            bars=4,
            tags=["inner voice", "sustain"],
        )
    )

    sync_pattern = [
        ["B1"],
        ["T1", "T2"],
        ["B2"],
        [],
        ["B1"],
        ["T3", "T2"],
        ["B2"],
        ["T1"],
    ]
    lessons.append(
        lesson(
            "09-syncopated-pinch-exercise",
            "09. Syncopated Pinch Exercise",
            "syncopation",
            "Feel off-beat pinches without losing the pulse.",
            "Count strictly. The whole point is to keep time while the accents land in less comfortable places.",
            72,
            prog,
            "syncopated pinch",
            make_events_from_progression(prog, sync_pattern),
            bars=4,
            tags=["syncopation", "pinch"],
        )
    )

    ring_pattern = [
        ["B1", "T1"],
        ["T3"],
        ["T2"],
        ["B2"],
        ["T1", "T2"],
        ["T3"],
        ["B1"],
        ["T2"],
    ]
    lessons.append(
        lesson(
            "10-ring-through-chord-study",
            "10. Ring-Through Chord Study",
            "sustain / ring-through",
            "Let notes sustain instead of chopping them off.",
            "Once a treble note is down, keep it alive as long as the shape allows. This is where the texture starts to sound musical.",
            62,
            ["Cmaj7", "G/B", "Am", "Fmaj7"],
            "ring-through arpeggio",
            make_events_from_progression(["Cmaj7", "G/B", "Am", "Fmaj7"], ring_pattern),
            bars=4,
            tags=["sustain", "texture"],
        )
    )

    accent_pattern = [
        ["B1"],
        ["T1"],
        ["B2"],
        ["T2"],
        ["B1"],
        ["T1", "T2"],
        ["B2"],
        ["T3"],
    ]
    lessons.append(
        lesson(
            "11-thumb-accent-dynamic-control",
            "11. Thumb Accent / Dynamic Control",
            "dynamics",
            "Practice making bass, melody, or both sit forward on command.",
            "Run the same pattern three ways: bass-heavy, melody-heavy, then even. The movement is the same, only the emphasis changes.",
            68,
            prog,
            "dynamic study",
            make_events_from_progression(prog, accent_pattern),
            bars=4,
            tags=["dynamics", "control"],
        )
    )

    prep_pattern = [
        ["B1", "T1"],
        ["T3"],
        ["B2", "T2"],
        ["T1"],
        ["B1", "T1", "T2"],
        ["T3"],
        ["B2"],
        ["T2"],
    ]
    prep_prog = ["Cmaj7", "G/B", "Am", "Fmaj7"]
    lessons.append(
        lesson(
            "12-angeles-prep-etude",
            "12. Angeles Prep Etude",
            "Elliott-ish arpeggio study",
            "Combine bass motion, simultaneous plucks, and ringing treble notes inside one stable frame.",
            "This is the bridge exercise. The right hand should feel repetitive and reliable while the harmony shifts under it.",
            76,
            prep_prog,
            "prep etude",
            make_events_from_progression(prep_prog, prep_pattern),
            bars=4,
            tags=["etude", "angeles-prep"],
        )
    )

    angeles_prog = ["Cmaj7", "G/B", "Am7", "Fmaj7", "Cmaj7", "Em7", "Am7", "Fmaj7"]
    custom = []
    pattern = [
        ["B1", "T1"],
        {"G": "0"},
        ["B2", "T2"],
        {"B": "1"},
        ["B1", "T1", "T2"],
        {"G": "0"},
        ["B2"],
        {"e": "3"},
    ]
    for bar_index, chord_name in enumerate(angeles_prog):
        bar_events = make_events_from_progression([chord_name], pattern)
        for evt in bar_events:
            evt.step += bar_index * 8
        custom.extend(bar_events)
    lessons.append(
        lesson(
            "13-angeles-inspired-original-study",
            "13. Angeles-Inspired Original Study",
            "Elliott-ish arpeggio study",
            "An original study that leans into bass motion, held treble notes, and slightly wistful open-position color.",
            "This is not a transcription. Use it as a musical drill.",
            78,
            angeles_prog,
            "original Angeles-inspired study",
            custom,
            bars=8,
            tags=["original-study", "elliott-ish", "angeles-inspired"],
        )
    )

    return lessons


def build_generated_lesson(existing_count: int, config: dict) -> Lesson:
    focus = config["focus"]
    difficulty = config["difficulty"]
    bars = config["bars"]
    palette = config["palette"]
    pattern_family = config["pattern"]
    bpm = config["bpm"]

    progression = cycle_progression(PALETTES[palette], bars)
    pattern = PATTERN_TEMPLATES[pattern_family]

    if focus == "thumb stability":
        pattern = PATTERN_TEMPLATES["bass-only"]
    elif focus == "pinch control":
        pattern = PATTERN_TEMPLATES["pinch"]
    elif focus == "alternating bass":
        pattern = PATTERN_TEMPLATES["melody-over-bass"]
    elif focus == "syncopation":
        pattern = PATTERN_TEMPLATES["syncopated pinch"]
    elif focus == "sustain / ring-through":
        pattern = PATTERN_TEMPLATES["ring-through arpeggio"]

    if difficulty == "easy":
        bpm = max(48, bpm - 10)
    elif difficulty == "hard":
        bpm = min(140, bpm + 12)

    events = make_events_from_progression(progression, pattern)
    lesson_id = f"generated-{existing_count + 1:03d}"
    title = f"Generated Study {existing_count + 1:03d}"
    instructions = f"Generated focus: {focus}. Treat this like a looping drill, not a performance piece. Stay relaxed and keep the right hand movement compact."
    goal = f"Train {focus} with a {difficulty} pattern over {bars} bars."
    return lesson(
        lesson_id,
        title,
        focus,
        goal,
        instructions,
        bpm,
        progression,
        pattern_family,
        events,
        bars=bars,
        steps_per_bar=8,
        tags=["generated", focus, difficulty, pattern_family],
        generated=True,
    )


# --- Importer Logic ---
def parse_title_from_text(text: str) -> str:
    lines = text.splitlines()
    for line in lines[:20]:
        clean = line.strip()
        if not clean:
            continue
        m = re.match(r"^(?:title|artist|tab by|by)\s*:\s*(.+)", clean, re.I)
        if m:
            return m.group(1).strip()
        if len(clean) > 4 and clean == clean.upper():
            return clean
    for line in lines[:10]:
        if line.strip() and len(line.strip()) < 80:
            return line.strip()
    return "Untitled Import"


def extract_tab_blocks(text: str) -> List[List[str]]:
    lines = text.splitlines()

    def is_tab_line(l):
        l = l.strip()
        if not l:
            return False
        content = re.sub(r"^[eBGDAEebgdae1-6]\s*\|", "", l)
        if not content:
            return False
        if "-" not in content:
            return False
        valid_chars = set("-0123456789hps/\\| ")
        valid_count = sum(1 for c in content if c in valid_chars)
        return len(content) >= 10 and (valid_count / len(content) > 0.8)

    blocks, current_block = [], []
    for line in lines:
        if is_tab_line(line):
            current_block.append(line.strip())
            if len(current_block) == 6:
                blocks.append(current_block)
                current_block = []
        else:
            l = line.strip()
            if not (l.startswith("|") and "^" in l) and l != "":
                current_block = []
    return blocks


def parse_blocks_to_events(blocks: List[List[str]]) -> List[Event]:
    events, step_cursor = [], 0
    string_names = ["e", "B", "G", "D", "A", "E"]
    all_block_events, all_gaps = [], []

    for block in blocks:
        block_events = {}
        for i, line in enumerate(block):
            s_name = string_names[i]
            for match in re.finditer(r"(\d+)", line):
                pos = match.start()
                if pos not in block_events:
                    block_events[pos] = {}
                block_events[pos][s_name] = match.group()
        all_block_events.append(block_events)
        unique_pos = sorted(block_events.keys())
        all_gaps.extend(
            [unique_pos[i + 1] - unique_pos[i] for i in range(len(unique_pos) - 1)]
        )

    grid_size = (
        min([g for g in all_gaps if g >= 2]) if any(g >= 2 for g in all_gaps) else 4
    )

    for block_events in all_block_events:
        if not block_events:
            continue
        unique_pos = sorted(block_events.keys())
        block_start = unique_pos[0]
        for pos in unique_pos:
            rel_step = round((pos - block_start) / grid_size)
            events.append(Event(step=step_cursor + rel_step, notes=block_events[pos]))
        max_rel_step = round((unique_pos[-1] - block_start) / grid_size)
        step_cursor += max_rel_step + 8
    return events


# --- Audio Engine ---
def get_note_wav(string_name: str, fret: str) -> Optional[Path]:
    try:
        fret_val = int(fret)
    except (ValueError, TypeError):
        return None
    SOUND_DIR.mkdir(exist_ok=True)
    filepath = SOUND_DIR / f"{string_name}_{fret_val}.wav"
    if filepath.exists():
        return filepath

    base_freqs = {
        "E": 82.41,
        "A": 110.00,
        "D": 146.83,
        "G": 196.00,
        "B": 246.94,
        "e": 329.63,
    }
    base_f = base_freqs.get(string_name, 440.0)
    freq = base_f * (2 ** (fret_val / 12.0))
    sample_rate = 44100
    duration = 0.8
    n_samples = int(sample_rate * duration)
    decay = sample_rate * 0.4

    with wave.open(str(filepath), "w") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sample_rate)
        frames = bytearray(n_samples * 2)
        for i in range(n_samples):
            t = float(i) / sample_rate
            env = math.exp(-i / decay)
            val = math.sin(2 * math.pi * freq * t)
            struct.pack_into("<h", frames, i * 2, int(8000 * env * val))
        w.writeframesraw(frames)
    return filepath


# --- Helpers ---
def total_steps(lesson_obj: Lesson) -> int:
    if not lesson_obj.events:
        return lesson_obj.bars * lesson_obj.steps_per_bar
    return max(evt.step for evt in lesson_obj.events) + 1


def event_notes_by_step(lesson_obj: Lesson) -> Dict[int, Dict[str, str]]:
    return {evt.step: evt.notes for evt in lesson_obj.events}


def mode_interval_seconds(lesson_obj: Lesson, mode: str, bpm: int) -> float:
    if mode == "beat":
        return 60.0 / max(1, bpm)
    steps_per_beat = lesson_obj.steps_per_bar / 4.0
    return (60.0 / max(1, bpm)) / max(1.0, steps_per_beat)


def total_units(lesson_obj: Lesson, mode: str) -> int:
    if mode == "beat":
        return lesson_obj.bars * 4
    return total_steps(lesson_obj)


def active_steps_for_mode(lesson_obj: Lesson, mode: str, unit_index: int) -> List[int]:
    if mode == "beat":
        steps_per_beat = max(1, lesson_obj.steps_per_bar // 4)
        start = unit_index * steps_per_beat
        return list(range(start, min(start + steps_per_beat, total_steps(lesson_obj))))
    return [unit_index]


def beat_guide_for_step(lesson_obj: Lesson, step: int) -> str:
    local = step % lesson_obj.steps_per_bar
    if lesson_obj.steps_per_bar == 8:
        labels = ["1", "&", "2", "&", "3", "&", "4", "&"]
        return labels[local]
    per_beat = max(1, lesson_obj.steps_per_bar // 4)
    if local % per_beat == 0:
        return str((local // per_beat) + 1)
    return "."


def safe_addstr(stdscr, y: int, x: int, text: str, attr: int = 0):
    h, w = stdscr.getmaxyx()
    if y < 0 or y >= h or x >= w:
        return
    clipped = text[: max(0, w - x - 1)]
    if clipped:
        try:
            stdscr.addstr(y, x, clipped, attr)
        except curses.error:
            pass


class TrainerApp:
    def __init__(self, stdscr, audio_backend="auto"):
        self.stdscr = stdscr
        self.view = "library"
        self.library_index = 0
        self.player_index = 0
        self.playing = False
        self.playhead = 0
        self.split_view = True
        self.timing_mode_index = 1
        self.loop_lesson = False
        self.importer_url = ""
        self.importer_mode = "url"
        self.rename_mode = False
        self.rename_buffer = ""
        self.confirm_delete = False

        self.play_metronome = False
        self.play_audio = True
        self.audio_backend = audio_backend
        self.current_notes_map = {}

        self.loop_a = None
        self.loop_b = None
        self.speed_trainer = False
        self.speed_increment = 2
        self.speed_freq = 4
        self.loop_count = 0

        self.last_tick = time.time()
        self.lessons = build_builtin_lessons() + self.load_generated_lessons()

        self.generator_field = 0
        self.generator_values = {
            "focus": 0,
            "difficulty": 1,
            "bars": 1,
            "palette": 2,
            "pattern": 3,
            "bpm": 1,
        }
        self.status = "Ready."
        self.sound_cache = {}
        self.audio_backend = None
        self.sample_rate = 44100
        self.init_audio()

    def generate_tone(
        self, freq: float, duration: float = 0.3, volume: float = 0.5
    ) -> np.ndarray:
        if np is None:
            return None
        t = np.linspace(0, duration, int(self.sample_rate * duration), False)
        envelope = np.exp(-t / (duration * 0.4))
        tone = np.sin(2 * np.pi * freq * t) * envelope * volume
        return tone.astype(np.float32)

    def init_audio(self):
        if self.audio_backend == "pygame" and pygame is not None:
            try:
                pygame.mixer.pre_init(44100, -16, 2, 512)
                pygame.init()
                pygame.mixer.init()
                self.pygame_ready = True
            except Exception:
                self.pygame_ready = False
        elif self.audio_backend == "sounddevice" and sd is not None and np is not None:
            try:
                sd.play(np.zeros(1), self.sample_rate)
                sd.stop()
            except Exception:
                pass
        elif self.audio_backend == "simpleaudio" and sa is not None:
            SOUND_DIR.mkdir(exist_ok=True)

    def play_note_pygame(self, freq: float):
        if not hasattr(self, "pygame_ready") or not self.pygame_ready:
            return
        try:
            tone = self.generate_tone(freq, 0.3, 0.4)
            if tone is not None:
                import io
                import wave as wave_module

                buffer = io.BytesIO()
                with wave_module.open(buffer, "w") as w:
                    w.setnchannels(1)
                    w.setsampwidth(2)
                    w.setframerate(self.sample_rate)
                    w.writeframes(tone.astype(np.int16).tobytes())
                buffer.seek(0)
                sound = pygame.mixer.Sound(buffer)
                sound.play()
        except Exception:
            pass

    def play_note_sounddevice(self, freq: float):
        try:
            tone = self.generate_tone(freq, 0.3, 0.4)
            if tone is not None:
                sd.play(tone, self.sample_rate)
                sd.sleep(50)
        except Exception:
            pass

    def play_note_simpleaudio(self, freq: float):
        try:
            tone = self.generate_tone(freq, 0.3, 0.4)
            if tone is not None:
                import io
                import wave as wave_module

                buffer = io.BytesIO()
                with wave_module.open(buffer, "w") as w:
                    w.setnchannels(1)
                    w.setsampwidth(2)
                    w.setframerate(self.sample_rate)
                    w.writeframes(tone.astype(np.int16).tobytes())
                buffer.seek(0)
                wave_obj = sa.WaveObject.from_wave_file(buffer)
                wave_obj.play()
        except Exception:
            pass

    def play_note_afplay(self, freq: float):
        import subprocess

        try:
            SOUND_DIR.mkdir(exist_ok=True)
            path = SOUND_DIR / f"temp_{int(freq)}.wav"
            tone = self.generate_tone(freq, 0.3, 0.4)
            if tone is not None:
                import wave as wave_module

                with wave_module.open(str(path), "w") as w:
                    w.setnchannels(1)
                    w.setsampwidth(2)
                    w.setframerate(self.sample_rate)
                    w.writeframes(tone.astype(np.int16).tobytes())
                subprocess.Popen(
                    ["afplay", "-q", "1", str(path)],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
        except Exception:
            pass

    def get_frequency(self, string_name: str, fret: str) -> float:
        base_freqs = {
            "E": 82.41,
            "A": 110.00,
            "D": 146.83,
            "G": 196.00,
            "B": 246.94,
            "e": 329.63,
        }
        try:
            fret_val = int(fret)
        except (ValueError, TypeError):
            fret_val = 0
        base_f = base_freqs.get(string_name, 440.0)
        return base_f * (2 ** (fret_val / 12.0))

    def play_metronome_sound(self):
        freq = 880
        if self.audio_backend == "pygame":
            self.play_note_pygame(freq)
        elif self.audio_backend == "sounddevice":
            self.play_note_sounddevice(freq)
        elif self.audio_backend == "simpleaudio":
            self.play_note_simpleaudio(freq)
        elif self.audio_backend == "afplay":
            import subprocess

            try:
                SOUND_DIR.mkdir(exist_ok=True)
                m_path = SOUND_DIR / "metronome.wav"
                if not m_path.exists():
                    import wave

                    n_samples = int(self.sample_rate * 0.05)
                    frames = bytearray(n_samples * 2)
                    for i in range(n_samples):
                        t = i / self.sample_rate
                        env = math.exp(-t / 0.015)
                        val = math.sin(2 * math.pi * 880 * t)
                        struct.pack_into("<h", frames, i * 2, int(2000 * env * val))
                    with wave.open(str(m_path), "w") as w:
                        w.setnchannels(1)
                        w.setsampwidth(2)
                        w.setframerate(self.sample_rate)
                        w.writeframesraw(frames)
                subprocess.Popen(
                    ["afplay", "-q", "1", str(m_path)],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            except Exception:
                pass

    def play_note_sound(self, string_name: str, fret: str):
        freq = self.get_frequency(string_name, fret)
        if self.audio_backend == "pygame":
            self.play_note_pygame(freq)
        elif self.audio_backend == "sounddevice":
            self.play_note_sounddevice(freq)
        elif self.audio_backend == "simpleaudio":
            self.play_note_simpleaudio(freq)
        elif self.audio_backend == "afplay":
            self.play_note_afplay(freq)

    def load_generated_lessons(self) -> List[Lesson]:
        lessons = []
        for path in sorted(generated_dir().glob("*.json")):
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
                lessons.append(Lesson.from_dict(payload))
            except Exception:
                continue
        return lessons

    def save_lesson(self, lesson_obj: Lesson):
        path = generated_dir() / f"{lesson_obj.lesson_id}.json"
        path.write_text(lesson_obj.to_json(), encoding="utf-8")

    def reload_generated(self):
        builtins = [ls for ls in self.lessons if not ls.generated]
        self.lessons = builtins + self.load_generated_lessons()
        self.library_index = min(self.library_index, len(self.lessons) - 1)
        self.status = "Reloaded generated lessons."

    def delete_current_lesson(self):
        lesson_obj = self.lessons[self.library_index]
        if not lesson_obj.generated:
            self.status = "Cannot delete built-in lessons."
            return
        path = generated_dir() / f"{lesson_obj.lesson_id}.json"
        if path.exists():
            path.unlink()
        self.reload_generated()
        self.status = f"Deleted {lesson_obj.title}."

    def launch_player(self, index: int):
        self.player_index = max(0, min(index, len(self.lessons) - 1))
        self.view = "player"
        self.playing = False
        self.loop_a = None
        self.loop_b = None
        self.loop_count = 0
        self.current_notes_map = event_notes_by_step(self.lessons[self.player_index])
        self.playhead = 0
        self.last_tick = time.time()
        if self.play_audio:
            for step, notes in self.current_notes_map.items():
                for s_name, fret in notes.items():
                    get_note_wav(s_name, fret)

    @property
    def timing_mode(self) -> str:
        return TIMING_MODES[self.timing_mode_index]

    @property
    def current_lesson(self) -> Lesson:
        return self.lessons[self.player_index]

    def step_playback(self):
        if not self.playing or self.view != "player":
            return
        lesson_obj = self.current_lesson
        total = total_units(lesson_obj, self.timing_mode)
        end_limit = self.loop_b if self.loop_b is not None else total
        interval = mode_interval_seconds(lesson_obj, self.timing_mode, lesson_obj.bpm)
        now = time.time()

        while now - self.last_tick >= interval:
            if self.timing_mode == "beat" or (
                self.playhead % (lesson_obj.steps_per_bar // 4) == 0
            ):
                if self.play_metronome:
                    self.play_metronome_sound()

            if self.play_audio:
                notes = self.current_notes_map.get(self.playhead, {})
                for string_name, fret in notes.items():
                    self.play_note_sound(string_name, fret)

            self.playhead += 1
            self.last_tick += interval

            if self.playhead >= end_limit:
                self.loop_count += 1
                if self.speed_trainer and self.loop_count % self.speed_freq == 0:
                    self.current_lesson.bpm = min(
                        180, self.current_lesson.bpm + self.speed_increment
                    )
                    self.status = f"Speed up! BPM: {self.current_lesson.bpm}"

                if self.loop_lesson or self.loop_a is not None:
                    self.playhead = self.loop_a if self.loop_a is not None else 0
                    self.status = "Looped."
                else:
                    self.playhead = total - 1 if total else 0
                    self.playing = False
                    self.status = "Finished."
                break

    def draw(self):
        self.stdscr.erase()
        height, width = self.stdscr.getmaxyx()
        if height < 18 or width < 70:
            safe_addstr(self.stdscr, 1, 2, f"{APP_NAME}", curses.A_BOLD)
            safe_addstr(
                self.stdscr, 3, 2, "Terminal is too small. Resize to at least 70x18."
            )
            safe_addstr(self.stdscr, height - 2, 2, "q: quit")
            self.stdscr.refresh()
            return

        if self.view == "library":
            self.draw_library()
        elif self.view == "player":
            self.draw_player()
        elif self.view == "generator":
            self.draw_generator()
        elif self.view == "importer":
            self.draw_importer()

        footer = self.status[: max(0, width - 2)]
        safe_addstr(self.stdscr, height - 1, 1, footer, curses.A_DIM)
        self.stdscr.refresh()

    def draw_header(self, title: str, subtitle: str = ""):
        safe_addstr(self.stdscr, 0, 2, APP_NAME, curses.A_BOLD)
        safe_addstr(self.stdscr, 1, 2, title, curses.A_UNDERLINE)
        if subtitle:
            safe_addstr(self.stdscr, 2, 2, subtitle)

    def draw_wrapped_block(
        self, y: int, x: int, width: int, text: str, attr: int = 0
    ) -> int:
        lines = textwrap.wrap(text, width=max(10, width)) or [""]
        for offset, line in enumerate(lines):
            safe_addstr(self.stdscr, y + offset, x, line, attr)
        return len(lines)

    def draw_library(self):
        h, w = self.stdscr.getmaxyx()
        self.draw_header("Lesson Library", "Open a lesson, generate, or import.")
        top = 4
        visible = h - 7
        start = max(0, self.library_index - visible // 2)
        end = min(len(self.lessons), start + visible)

        safe_addstr(
            self.stdscr,
            top - 1,
            2,
            "Title".ljust(38) + "Category".ljust(24) + "BPM  Goal",
            curses.A_BOLD,
        )
        for screen_row, idx in enumerate(range(start, end), start=top):
            lesson_obj = self.lessons[idx]
            attr = curses.A_REVERSE if idx == self.library_index else 0
            title = lesson_obj.title[:36].ljust(38)
            category = lesson_obj.category[:22].ljust(24)
            goal = lesson_obj.goal[: max(0, w - 72)]
            line = f"{title}{category}{str(lesson_obj.bpm).rjust(3)}  {goal}"
            safe_addstr(self.stdscr, screen_row, 2, line, attr)

        if self.rename_mode:
            safe_addstr(
                self.stdscr,
                h - 4,
                2,
                f"Rename to: {self.rename_buffer}_",
                curses.A_BOLD,
            )
            hints = "Enter to save | Esc to cancel"
        elif self.confirm_delete:
            safe_addstr(
                self.stdscr,
                h - 4,
                2,
                "Are you sure you want to delete this lesson? (y/n)",
                curses.A_BOLD | curses.A_BLINK,
            )
            hints = "y: delete | n: cancel"
        else:
            hints = "Enter open | g gen | i import | r rename | d del | q quit"
        safe_addstr(self.stdscr, h - 3, 2, hints, curses.A_DIM)

    def draw_player(self):
        h, w = self.stdscr.getmaxyx()
        lesson_obj = self.current_lesson
        mode = self.timing_mode
        loop_str = f"A:{self.loop_a if self.loop_a is not None else '-'} B:{self.loop_b if self.loop_b is not None else '-'}"
        speed_str = f"speed:{'ON' if self.speed_trainer else 'OFF'}"
        audio_str = f"metro:{'ON' if self.play_metronome else 'OFF'} audio:{'ON' if self.play_audio else 'OFF'}"

        self.draw_header(
            lesson_obj.title,
            f"BPM {lesson_obj.bpm} | {mode} | {audio_str} | loop: {loop_str} | {speed_str}",
        )

        tab_top = 4
        if self.split_view:
            row = 4
            row += self.draw_wrapped_block(
                row, 2, w - 4, f"Goal: {lesson_obj.goal}", curses.A_BOLD
            )
            row += self.draw_wrapped_block(
                row + 1, 2, w - 4, f"Instructions: {lesson_obj.instructions}"
            )
            tab_top = row + 2

        self.draw_tab(tab_top, 2, w - 4, lesson_obj)
        self.draw_fretboard(tab_top + 11, 2, w - 4, lesson_obj)

        hints = "space play | m metro | p audio | a/b marks | s speed | v split | +/- bpm | [ ] lesson | l loop | q back"
        safe_addstr(self.stdscr, h - 3, 2, hints[: w - 4], curses.A_DIM)

    def draw_tab(self, y: int, x: int, width: int, lesson_obj: Lesson):
        total = total_steps(lesson_obj)
        active_steps = set(
            active_steps_for_mode(lesson_obj, self.timing_mode, self.playhead)
        )
        active_center = sorted(active_steps)[0] if active_steps else 0

        max_visible_steps = max(8, (width - 4) // CELL_WIDTH)
        start = max(0, active_center - max_visible_steps // 2)
        start = min(start, max(0, total - max_visible_steps))
        end = min(total, start + max_visible_steps)

        for step in range(start, end):
            label = beat_guide_for_step(lesson_obj, step)
            attr = curses.A_REVERSE if step in active_steps else curses.A_BOLD
            if step == self.loop_a:
                label = "A"
            if step == self.loop_b:
                label = "B"
            safe_addstr(
                self.stdscr,
                y,
                x + 2 + (step - start) * CELL_WIDTH,
                label.ljust(CELL_WIDTH),
                attr,
            )

        for row_offset, string_name in enumerate(STRING_ORDER, start=1):
            safe_addstr(
                self.stdscr, y + row_offset, x, f"{string_name}|", curses.A_BOLD
            )
            for step in range(start, end):
                notes = self.current_notes_map.get(step, {})
                fret = notes.get(string_name)
                cell = f"{fret if fret else '-'}{'-' * (CELL_WIDTH - (len(fret) if fret else 1))}"
                attr = curses.A_REVERSE if step in active_steps else 0
                safe_addstr(
                    self.stdscr,
                    y + row_offset,
                    x + 2 + (step - start) * CELL_WIDTH,
                    cell,
                    attr,
                )

        safe_addstr(self.stdscr, y + 7, x, "RIGHT:", curses.A_DIM)
        for step in range(start, end):
            notes = self.current_notes_map.get(step, {})
            fingers_used = set()
            for s_name in notes.keys():
                f = FINGER_LOOKUP.get(s_name.lower())
                if f is not None:
                    fingers_used.add(int(f))
            if fingers_used:
                finger_str = "".join(sorted(FINGER_NAMES[f] for f in fingers_used))
            else:
                finger_str = "-"
            attr = curses.A_REVERSE if step in active_steps else curses.A_DIM
            safe_addstr(
                self.stdscr,
                y + 7,
                x + 7 + (step - start) * CELL_WIDTH,
                finger_str.ljust(CELL_WIDTH),
                attr,
            )

    @staticmethod
    def fret_to_left_finger(fret_num: int) -> str:
        if fret_num == 0:
            return "T"
        elif fret_num <= 3:
            return "1"
        elif fret_num <= 6:
            return "2"
        elif fret_num <= 9:
            return "3"
        else:
            return "4"

    def draw_fretboard(self, y: int, x: int, width: int, lesson_obj: Lesson):
        safe_addstr(
            self.stdscr,
            y,
            x,
            "LEFT HAND: fretting (0=T 1=I 2=M 3=R 4=P)",
            curses.A_BOLD | curses.A_DIM,
        )
        active_steps = active_steps_for_mode(
            lesson_obj, self.timing_mode, self.playhead
        )
        current_notes = {}
        for s in active_steps:
            current_notes.update(self.current_notes_map.get(s, {}))

        fret_w = 4
        num_frets = min(15, (width - 10) // fret_w)

        for f in range(num_frets + 1):
            safe_addstr(
                self.stdscr,
                y + 1,
                x + 4 + f * fret_w,
                str(f).center(fret_w),
                curses.A_DIM,
            )

        for i, s_name in enumerate(STRING_ORDER):
            safe_addstr(self.stdscr, y + 2 + i, x, f"{s_name}|", curses.A_BOLD)
            active_fret = current_notes.get(s_name)
            for f in range(num_frets + 1):
                if active_fret == str(f):
                    char = self.fret_to_left_finger(f)
                    attr = curses.A_REVERSE | curses.A_BOLD
                else:
                    char = "-"
                    attr = 0
                safe_addstr(
                    self.stdscr, y + 2 + i, x + 4 + f * fret_w, f" {char} |", attr
                )

    def draw_importer(self):
        self.draw_header(
            "Importer", f"Mode: {self.importer_mode.upper()} (Tab to switch)"
        )
        h, w = self.stdscr.getmaxyx()
        prompt = "Enter URL:" if self.importer_mode == "url" else "Enter File Path:"
        safe_addstr(self.stdscr, 5, 4, prompt, curses.A_BOLD)
        safe_addstr(self.stdscr, 6, 4, self.importer_url + "_")
        help_text = (
            "Instructions: Paste a URL or local file path to extract tab blocks."
        )
        self.draw_wrapped_block(8, 4, w - 8, help_text, curses.A_DIM)
        hints = "Type | Tab switch mode | Enter fetch | q back"
        safe_addstr(self.stdscr, h - 3, 2, hints[: w - 4], curses.A_DIM)

    def draw_generator(self):
        self.draw_header("Generator", "Build a new drill.")
        h, w = self.stdscr.getmaxyx()
        fields = [
            ("focus", FOCUS_OPTIONS[self.generator_values["focus"]]),
            ("difficulty", DIFFICULTY_OPTIONS[self.generator_values["difficulty"]]),
            ("bars", str(BAR_OPTIONS[self.generator_values["bars"]])),
            ("palette", PALETTE_OPTIONS[self.generator_values["palette"]]),
            ("pattern", PATTERN_OPTIONS[self.generator_values["pattern"]]),
            ("bpm", str(BPM_OPTIONS[self.generator_values["bpm"]])),
        ]
        top = 5
        for idx, (label, current) in enumerate(fields):
            attr = curses.A_REVERSE if idx == self.generator_field else 0
            safe_addstr(self.stdscr, top + idx * 2, 4, f"{label:<18} {current}", attr)
        hints = "arrows change | Enter generate | q back"
        safe_addstr(self.stdscr, h - 3, 2, hints[: w - 4], curses.A_DIM)

    def handle_key(self, ch: int):
        if ch == -1:
            return True
        if self.view == "library":
            return self.handle_library_key(ch)
        if self.view == "player":
            return self.handle_player_key(ch)
        if self.view == "generator":
            return self.handle_generator_key(ch)
        if self.view == "importer":
            return self.handle_importer_key(ch)
        return True

    def handle_library_key(self, ch: int):
        if self.rename_mode:
            if ch in (27,):
                self.rename_mode = False
                self.status = "Rename cancelled."
            elif ch in (10, 13, curses.KEY_ENTER):
                if self.rename_buffer.strip():
                    lesson = self.lessons[self.library_index]
                    lesson.title = self.rename_buffer.strip()
                    self.save_lesson(lesson)
                    self.status = f"Renamed to {lesson.title}"
                self.rename_mode = False
            elif ch in (curses.KEY_BACKSPACE, 127, 8):
                self.rename_buffer = self.rename_buffer[:-1]
            elif 32 <= ch <= 126:
                self.rename_buffer += chr(ch)
            return True

        if self.confirm_delete:
            if ch in (ord("y"), ord("Y")):
                self.delete_current_lesson()
            elif ch in (ord("n"), ord("N"), 27):
                self.status = "Deletion cancelled."
            self.confirm_delete = False
            return True

        if ch in (ord("q"), 27):
            return False
        if ch in (curses.KEY_DOWN, ord("j")):
            self.library_index = min(len(self.lessons) - 1, self.library_index + 1)
        elif ch in (curses.KEY_UP, ord("k")):
            self.library_index = max(0, self.library_index - 1)
        elif ch in (10, 13, curses.KEY_ENTER):
            self.launch_player(self.library_index)
        elif ch == ord("g"):
            self.view = "generator"
            self.playing = False
        elif ch == ord("i"):
            self.view = "importer"
            self.playing = False
        elif ch == ord("r"):
            lesson = self.lessons[self.library_index]
            if lesson.generated:
                self.rename_mode = True
                self.rename_buffer = ""
            else:
                self.status = "Cannot rename built-in lessons."
        elif ch == ord("d"):
            lesson = self.lessons[self.library_index]
            if lesson.generated:
                self.confirm_delete = True
            else:
                self.status = "Cannot delete built-in lessons."
        return True

    def handle_player_key(self, ch: int):
        if ch in (ord("q"), 27):
            self.view = "library"
            self.playing = False
            return True
        if ch == ord(" "):
            self.playing = not self.playing
            self.last_tick = time.time()
            self.status = "Playing." if self.playing else "Paused."
        elif ch == ord("0"):
            self.playhead = self.loop_a if self.loop_a is not None else 0
            self.status = "Restarted."
        elif ch == ord("v"):
            self.split_view = not self.split_view
        elif ch == ord("t"):
            self.timing_mode_index = (self.timing_mode_index + 1) % len(TIMING_MODES)
        elif ch in (ord("+"), ord("=")):
            self.current_lesson.bpm = min(180, self.current_lesson.bpm + 2)
        elif ch == ord("-"):
            self.current_lesson.bpm = max(30, self.current_lesson.bpm - 2)
        elif ch == ord("["):
            self.launch_player((self.player_index - 1) % len(self.lessons))
        elif ch == ord("]"):
            self.launch_player((self.player_index + 1) % len(self.lessons))
        elif ch == ord("l"):
            self.loop_lesson = not self.loop_lesson
        elif ch == ord("a"):
            self.loop_a = self.playhead
            self.status = f"Marker A set at {self.playhead}"
        elif ch == ord("b"):
            self.loop_b = self.playhead
            if self.loop_b <= (self.loop_a or 0):
                self.loop_b = None
            self.status = f"Marker B set at {self.playhead}"
        elif ch == ord("c"):
            self.loop_a = self.loop_b = None
            self.status = "Markers cleared."
        elif ch == ord("s"):
            self.speed_trainer = not self.speed_trainer
        elif ch == ord("m"):
            self.play_metronome = not self.play_metronome
        elif ch == ord("p"):
            self.play_audio = not self.play_audio
        return True

    def handle_generator_key(self, ch: int):
        if ch in (ord("q"), 27):
            self.view = "library"
            return True
        if ch in (curses.KEY_DOWN, ord("j")):
            self.generator_field = min(5, self.generator_field + 1)
        elif ch in (curses.KEY_UP, ord("k")):
            self.generator_field = max(0, self.generator_field - 1)
        elif ch in (curses.KEY_LEFT, ord("h")):
            key = ["focus", "difficulty", "bars", "palette", "pattern", "bpm"][
                self.generator_field
            ]
            limits = {
                "focus": len(FOCUS_OPTIONS),
                "difficulty": len(DIFFICULTY_OPTIONS),
                "bars": len(BAR_OPTIONS),
                "palette": len(PALETTE_OPTIONS),
                "pattern": len(PATTERN_OPTIONS),
                "bpm": len(BPM_OPTIONS),
            }
            self.generator_values[key] = (self.generator_values[key] - 1) % limits[key]
        elif ch in (curses.KEY_RIGHT, ord("l")):
            key = ["focus", "difficulty", "bars", "palette", "pattern", "bpm"][
                self.generator_field
            ]
            limits = {
                "focus": len(FOCUS_OPTIONS),
                "difficulty": len(DIFFICULTY_OPTIONS),
                "bars": len(BAR_OPTIONS),
                "palette": len(PALETTE_OPTIONS),
                "pattern": len(PATTERN_OPTIONS),
                "bpm": len(BPM_OPTIONS),
            }
            self.generator_values[key] = (self.generator_values[key] + 1) % limits[key]
        elif ch in (10, 13, curses.KEY_ENTER):
            cfg = {
                "focus": FOCUS_OPTIONS[self.generator_values["focus"]],
                "difficulty": DIFFICULTY_OPTIONS[self.generator_values["difficulty"]],
                "bars": BAR_OPTIONS[self.generator_values["bars"]],
                "palette": PALETTE_OPTIONS[self.generator_values["palette"]],
                "pattern": PATTERN_OPTIONS[self.generator_values["pattern"]],
                "bpm": BPM_OPTIONS[self.generator_values["bpm"]],
            }
            gen_count = len([ls for ls in self.lessons if ls.generated])
            new_lesson = build_generated_lesson(gen_count, cfg)
            self.save_lesson(new_lesson)
            self.reload_generated()
            self.launch_player(len(self.lessons) - 1)
            self.status = f"Generated {new_lesson.title}."
        return True

    def handle_importer_key(self, ch: int):
        if ch in (ord("q"), 27):
            self.view = "library"
            return True
        elif ch == 9:  # Tab
            self.importer_mode = "file" if self.importer_mode == "url" else "url"
        elif ch in (curses.KEY_BACKSPACE, 127, 8):
            self.importer_url = self.importer_url[:-1]
        elif ch in (10, 13, curses.KEY_ENTER):
            if not self.importer_url:
                return True
            try:
                for ls in self.lessons:
                    if getattr(ls, "source", None) == self.importer_url:
                        self.status = "Already imported."
                        return True

                text = ""
                if self.importer_mode == "url":
                    req = urllib.request.Request(
                        self.importer_url, headers={"User-Agent": "Mozilla/5.0"}
                    )
                    text = (
                        urllib.request.urlopen(req, timeout=10)
                        .read()
                        .decode("utf-8", errors="ignore")
                    )
                else:
                    p = Path(self.importer_url).expanduser()
                    text = p.read_text(encoding="utf-8", errors="ignore")

                blocks = extract_tab_blocks(text)
                if not blocks:
                    raise ValueError("No playable tab blocks found.")
                events = parse_blocks_to_events(blocks)

                gen_count = len([ls for ls in self.lessons if ls.generated])
                new_lesson = lesson(
                    lesson_id=f"imported-{gen_count + 1:03d}",
                    title=parse_title_from_text(text),
                    category="import",
                    goal=f"Play along with {self.importer_url[:20]}",
                    instructions="Imported tab.",
                    bpm=80,
                    progression=["OPEN"],
                    pattern_name="imported",
                    events=events,
                    bars=1,
                    steps_per_bar=16,
                    tags=["imported"],
                    generated=True,
                    source=self.importer_url,
                )
                self.save_lesson(new_lesson)
                self.reload_generated()
                self.launch_player(len(self.lessons) - 1)
                self.status = f"Imported {new_lesson.title}."
            except Exception as e:
                self.status = f"Error: {e}"
        elif 32 <= ch <= 126:
            self.importer_url += chr(ch)
        return True

    def run(self):
        while True:
            self.step_playback()
            self.draw()
            self.stdscr.nodelay(True)
            ch = self.stdscr.getch()
            if ch != -1:
                curses.curs_set(1)
                if not self.handle_key(ch):
                    break
                curses.curs_set(0)
            time.sleep(0.01)


def main():
    pip_cmd = shutil.which("pip3") or shutil.which("pip")

    parser = argparse.ArgumentParser(description=f"{APP_NAME} v{VERSION}")
    parser.add_argument(
        "--validate", action="store_true", help="run non-interactive validation"
    )
    parser.add_argument(
        "--audio-backend",
        choices=["pygame", "sounddevice", "simpleaudio", "afplay", "auto"],
        default="auto",
        help="audio backend to use (default: auto)",
    )
    args = parser.parse_args()

    if args.validate:
        print("Validation OK")
        return

    backend = args.audio_backend
    if backend == "auto":
        if pygame is not None:
            backend = "pygame"
        elif sd is not None and np is not None:
            backend = "sounddevice"
        elif sa is not None:
            backend = "simpleaudio"
        else:
            backend = "afplay"

    print(f"Using audio backend: {backend}")

    if pygame is None and backend == "pygame":
        print(f"--- {APP_NAME} v{VERSION} Dependency Warning ---")
        print("The 'pygame' library is required for pygame audio backend.")
        if pip_cmd:
            install_cmd = f"{pip_cmd} install pygame"
            answer = input(f"Would you like to run '{install_cmd}' now? [Y/n] ")
            if answer.lower().strip() in ["y", "yes", ""]:
                os.system(install_cmd)
                print("\nInstallation complete. Re-launching app...")
                import sys

                os.execv(sys.executable, [sys.executable] + sys.argv)
            else:
                print("Audio will be disabled.")
        else:
            print("Could not find 'pip' or 'pip3'. Please install pygame manually.")
        input("Press Enter to continue...")

    curses.wrapper(lambda stdscr: TrainerApp(stdscr, backend).run())


if __name__ == "__main__":
    main()
