import random
import time

from fer import FER
import cv2
import vlc


def create_media(instance, emotion, intensity):
    if emotion not in ["happy", "angry", "sad", "neutral"]:
        emotion = "neutral"
    if intensity < 0.3:
        emotion = "neutral"
    return instance.media_new(f"sounds/{emotion}0{random.randint(1, 2)}.ogg")


def main():
    cam = cv2.VideoCapture(1)
    detector = FER()
    instance = vlc.Instance()
    player = instance.media_player_new()
    while True:
        _, img = cam.read()
        (emotion, intensity) = detector.top_emotion(img)
        if emotion is not None:
            print(emotion, intensity)

            player.set_media(create_media(instance, emotion, intensity))

            player.play()
            time.sleep(5)
        if cv2.waitKey(1) == 27:
            break  # esc to quit
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
