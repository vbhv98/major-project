from scipy.spatial import distance as dist
from imutils.video import FileVideoStream
from imutils.video import VideoStream
from imutils import face_utils
from datetime import datetime
import numpy as np
import imutils
import time
import dlib
import json
import cv2
import sys
import os


def log(message):
    print(message)
    sys.stdout.flush()


def beep():
    os.system('mpg123 -q ./scripts/beep-07.mp3')


def eye_aspect_ratio(eye):

    A = dist.euclidean(eye[1], eye[5])
    B = dist.euclidean(eye[2], eye[4])

    C = dist.euclidean(eye[0], eye[3])

    ear = (A + B) / (2.0 * C)

    return ear


blinked = True
blinked_s = True
blinked_m = True

blinkstart = True

EYE_AR_THRESH = 0.28
EYE_AR_CONSEC_FRAMES_S = 10
EYE_AR_CONSEC_FRAMES_M = 20
EYE_AR_CONSEC_FRAMES_L = 30

COUNTER = 0

log(json.dumps({"type": "INFO", "msg": "Loading LandMark Resource"}))
detector = dlib.get_frontal_face_detector()
predictor = dlib.shape_predictor(
    "./scripts/shape_predictor_68_face_landmarks.dat")

(lStart, lEnd) = face_utils.FACIAL_LANDMARKS_IDXS["left_eye"]
(rStart, rEnd) = face_utils.FACIAL_LANDMARKS_IDXS["right_eye"]

log(json.dumps({"type": "INFO", "msg": "Starting Video"}))

fileStream = True
vs = VideoStream(src=0).start()

fileStream = False
time.sleep(1.0)

while True:
    time.sleep(0.04)
    if fileStream and not vs.more():
        break

    frame = vs.read()

    frame = cv2.flip(frame, 1)
    frame = imutils.resize(frame, width=400)
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    rects = detector(gray, 0)

    for rect in rects:

        shape = predictor(gray, rect)
        shape = face_utils.shape_to_np(shape)

        leftEye = shape[lStart:lEnd]
        rightEye = shape[rStart:rEnd]
        leftEAR = eye_aspect_ratio(leftEye)
        rightEAR = eye_aspect_ratio(rightEye)

        ear = (leftEAR + rightEAR) / 2.0

        leftEyeHull = cv2.convexHull(leftEye)
        rightEyeHull = cv2.convexHull(rightEye)
        cv2.drawContours(frame, [leftEyeHull], -1, (0, 255, 0), 1)
        cv2.drawContours(frame, [rightEyeHull], -1, (0, 255, 0), 1)

        if not blinked and ear < EYE_AR_THRESH:
            COUNTER += 1
            if COUNTER == 2:
                blinkstart = True
            else:
                blinkstart = False
            if COUNTER >= EYE_AR_CONSEC_FRAMES_L:
                blinked = True
                beep()
                log(json.dumps({"type": "BLINK", "msg": "L"}))
            elif not blinked_m and COUNTER >= EYE_AR_CONSEC_FRAMES_M:
                blinked_m = True
                beep()
                log(json.dumps({"type": "BLINK", "msg": "M"}))
            elif not blinked_s and COUNTER >= EYE_AR_CONSEC_FRAMES_S:
                blinked_s = True
                beep()
                log(json.dumps({"type": "BLINK", "msg": "S"}))

        else:
            blinkstart, blinked, blinked_m, blinked_s = False, False, False, False
            COUNTER = 0
        cv2.putText(frame, "EAR: {:.2f}".format(ear), (260, 25),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

    cv2.imshow("Frame", frame)
    key = cv2.waitKey(1) & 0xFF

    if key == ord("q"):
        break

cv2.destroyAllWindows()

vs.stop()
