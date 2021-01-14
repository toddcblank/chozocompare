import cv2
import numpy as np
import time


class Video:
    videoFilename = ""
    videoStartTime = 0
    gameplayCrop = [(0, 0), (540, 380)]

# This file makes it easier to find the right bounding box for a video

if __name__ == '__main__':

    testVideo = Video()
    testVideo.videoFilename = "../Oatsngoats-4146.mp4"
    testVideo.videoStartTime = 15 + 15 * 60
    testVideo.gameplayCrop = [(173, 1), (536, 357)]

    cap = cv2.VideoCapture(testVideo.videoFilename)
    startFrames = testVideo.videoStartTime * cap.get(cv2.CAP_PROP_FPS)
    cap.set(cv2.CAP_PROP_POS_FRAMES, startFrames)
    ret, frame = cap.read()
    frame = cv2.resize(frame, (540, 380), fx=0, fy=0, interpolation=cv2.INTER_CUBIC)
    cv2.rectangle(frame, testVideo.gameplayCrop[0], testVideo.gameplayCrop[1], (255,255,255), 1)
    cv2.imshow("Bounding Box", frame)

    while True:
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
