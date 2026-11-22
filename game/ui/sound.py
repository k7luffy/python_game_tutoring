"""Tiny procedural sound effects.  Audio is optional: if the mixer cannot
start (headless machines, no sound card) every call becomes a no-op."""

from __future__ import annotations

import math
from array import array

import pygame

RATE = 22050


def _tone(freq_start: float, freq_end: float, seconds: float, volume: float = 0.32,
          wave: str = "square") -> bytes:
    samples = array("h")
    count = int(RATE * seconds)
    phase = 0.0
    for index in range(count):
        t = index / max(1, count - 1)
        freq = freq_start + (freq_end - freq_start) * t
        phase += freq / RATE
        if wave == "square":
            value = 1.0 if (phase % 1.0) < 0.5 else -1.0
        elif wave == "saw":
            value = 2.0 * (phase % 1.0) - 1.0
        else:
            value = math.sin(phase * math.tau)
        envelope = min(1.0, t * 14.0) * (1.0 - t) ** 1.6
        samples.append(int(32767 * volume * envelope * value))
    return samples.tobytes()


def _sequence(notes: list[tuple[float, float]], gap: float = 0.0) -> bytes:
    data = bytearray()
    for frequency, seconds in notes:
        data.extend(_tone(frequency, frequency, seconds, 0.3, "square"))
        if gap:
            data.extend(bytes(int(RATE * gap) * 2))
    return bytes(data)


class SoundBank:
    def __init__(self) -> None:
        self.available = False
        self.enabled = True
        self._sounds: dict[str, pygame.mixer.Sound] = {}
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=RATE, size=-16, channels=1, buffer=512)
            pygame.mixer.set_num_channels(8)
            self.available = True
        except Exception:
            self.available = False
        if self.available:
            self._build()

    def _add(self, name: str, data: bytes) -> None:
        try:
            self._sounds[name] = pygame.mixer.Sound(buffer=data)
        except Exception:
            pass

    def _build(self) -> None:
        self._add("step", _tone(520, 460, 0.05, 0.16, "triangle"))
        self._add("turn", _tone(380, 520, 0.06, 0.16))
        self._add("bump", _tone(150, 70, 0.16, 0.35, "saw"))
        self._add("coin", _sequence([(880, 0.05), (1320, 0.09)], 0.01))
        self._add("chest", _sequence([(660, 0.06), (880, 0.06), (1320, 0.14)], 0.01))
        self._add("base", _sequence([(523, 0.08), (659, 0.08), (784, 0.16)], 0.01))
        self._add("success", _sequence([(523, 0.09), (659, 0.09), (784, 0.09), (1046, 0.22)], 0.02))
        self._add("victory", _sequence([(523, 0.1), (659, 0.1), (784, 0.1), (1046, 0.14), (1318, 0.34)], 0.03))
        self._add("fail", _sequence([(392, 0.14), (294, 0.26)], 0.02))
        self._add("error", _tone(220, 110, 0.22, 0.3, "saw"))
        self._add("beam", _tone(220, 1400, 0.55, 0.3, "saw"))
        self._add("fizzle", _tone(700, 140, 0.4, 0.3, "saw"))
        self._add("click", _tone(700, 900, 0.04, 0.14))

    def play(self, name: str) -> None:
        if not (self.available and self.enabled):
            return
        sound = self._sounds.get(name)
        if sound is not None:
            try:
                sound.play()
            except Exception:
                pass

    def toggle(self) -> bool:
        self.enabled = not self.enabled
        return self.enabled
