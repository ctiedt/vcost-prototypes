from dataclasses import dataclass
from os import path
import random
import subprocess
import time

from fer import FER
import cv2
import vlc

import music21
from music21.stream import Stream
from music21 import stream
from music21 import scale

from music21.interval import Interval
from music21.note import Note
from music21.note import Rest
from music21.duration import Duration
from music21 import instrument
from music21.chord import Chord


@dataclass
class EmotionSnapshot:
    angry: float
    disgust: float
    fear: float
    happy: float
    sad: float
    surprise: float
    neutral: float

    def from_dict(data: dict):
        return EmotionSnapshot(
            data["angry"],
            data["disgust"],
            data["fear"],
            data["happy"],
            data["sad"],
            data["surprise"],
            data["neutral"],
        )


a_maj = scale.MajorScale('a')  # [57, 59, 61, 62, 64, 66, 68]
g_min = scale.HarmonicMinorScale('e2')
motions = [-2, -1, -1, 0, 1, 1, 2]


def make_music(data: EmotionSnapshot, length: int) -> Stream:
    chords = stream.Part(
        [instrument.Piano(), music21.clef.TrebleClef()])
    high = stream.Part([instrument.Piano(), music21.clef.TrebleClef()])
    low = stream.Part([instrument.ElectricBass(), music21.clef.TrebleClef()])
    low_emph = stream.Part(
        [instrument.ElectricBass(), music21.clef.TrebleClef()])
    fear_track = stream.Part([instrument.Piano(), music21.clef.TrebleClef()])
    note = random.choice(a_maj.getPitches())
    low_note = random.choice(g_min.getPitches())
    cymbals = stream.Part(
        [instrument.Cymbals(), music21.clef.TrebleClef()])
    for i in range(length):
        note = note.transpose(Interval(random.choice(motions)))
        low_note = low_note.transpose(Interval(random.choice(motions)))
        if data.happy < 0.5:
            chords.append(Note(note, quarterLength=1))
        if data.happy > 0.5:
            high.append(Note(note.transpose(Interval(8)), quarterLength=0.5))
            high.append(Note(note.transpose(Interval(9)), quarterLength=0.5))
            # high.append(Rest(quarterLength=0.5))
        if i % 2 == 0 and data.angry > 0.3:
            low.append(Note(low_note, quarterLength=2))
            low_emph.append(
                Note(low_note.transpose(Interval(4)), quarterLengt=0.5))
            low_emph.append(Rest(quarterLengt=0.5))
        if data.fear > 0.3:
            # for i in range(4):
            #     fear_track.append(
            #         random.choice([Note(random.choice(g_min.getPitches()), quarterLength=0.5), Rest(quarterLength=0.5), Rest(quarterLength=0.5)]))
            cymbals.append(Note(quarterLength=1))

    complete = stream.Score()
    complete.insert(0, chords)
    complete.insert(0, high)
    complete.insert(0, low)
    complete.insert(0, low_emph)
    complete.insert(0, fear_track)
    complete.insert(0, cymbals)
    return complete


def main():
    cam = cv2.VideoCapture(1)
    detector = FER()
    instance = vlc.Instance()
    player = instance.media_player_new()

    if not any(path.exists(p) for p in ("fluidsynth/bin/fluidsynth", "fluidsynth/bin/fluidsynth.exe")):
        exit("Please download fluidsynth and place it in this folder or add the `fluidsynth` executable to your path")
    while True:
        _, img = cam.read()
        results = detector.detect_emotions(img)
        if len(results) > 0:
            snapshot = EmotionSnapshot.from_dict(results[0]["emotions"])
            print(snapshot)
            music = make_music(snapshot, 10)
            filename = music.write('mid')
            print(filename)
            subprocess.run(["fluidsynth/bin/fluidsynth.exe",
                           "-ni", "font.sf2", f"{filename}", "-F", f"{filename}.wav", "-R", "16000"])

            media = instance.media_new(f"{filename}.wav")
            player.set_media(media)
            player.play()
            time.sleep(5)
        if cv2.waitKey(1) == 27:
            break  # esc to quit
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
