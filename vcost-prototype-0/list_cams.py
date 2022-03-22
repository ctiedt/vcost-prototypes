import cv2
import sys

# Adapted from https://stackoverflow.com/a/61768256
def returnCameraIndexes(i):
    # checks the first 10 indexes.
    index = 0
    arr = []
    while i > 0:
        cap = cv2.VideoCapture(index)
        if cap.read()[0]:
            arr.append(index)
            cap.release()
        index += 1
        i -= 1
    return arr

def main():
    try:
        n_indexes = int(sys.argv[1])
    except IndexError:
        n_indexes = 10
    print(returnCameraIndexes(n_indexes))

if __name__ == "__main__":
    main()