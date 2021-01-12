import cv2
import numpy as np
import time

# Text Setup
# font
font = cv2.FONT_HERSHEY_SIMPLEX

# fontScale
fontScale = 1

# Blue color in BGR
color = (255, 255, 255)

# Line thickness of 1 px
thickness = 1

ENTERING_DOOR = 1
STILL_IN_DOOR = 2
EXITING_DOOR = 3
NOT_IN_DOOR = 4

# how many rooms to compare
roomsToCompare = 400

# Checks if we think we're in a door transition frame
# This currently naively checks if the middle part of the screen is dark.  So some rooms might be false positives
def check_for_door_state(video_frame, previous_frame, current_state):
    # cut out the hud of the gameplay
    gameplay_to_process = video_frame[60:, 0:].copy()

    # grab the four corners of the screen, which should avoid doors, but include lots
    # of colors from normal rooms
    ulBox = gameplay_to_process[0:100, 0:180]
    llBox = gameplay_to_process[-100:, 0:180]
    # lrBox = gameplay_to_process[-100:, -180:]
    lrBox = gameplay_to_process[-100:-20, -180:]
    urBox = gameplay_to_process[0:100, -180:]
    middleBox = gameplay_to_process[60:-60, 60:-60]

    # calculate the std of each box, if they're all low, then we probably have a door transition
    ulStd = np.std(ulBox)
    urStd = np.std(urBox)
    lrStd = np.std(lrBox)
    llStd = np.std(llBox)

    ulAvg = np.average(ulBox)
    urAvg = np.average(urBox)
    lrAvg = np.average(lrBox)
    llAvg = np.average(llBox)

    middleStd = np.std(middleBox)
    middleAvg = np.std(middleBox)

    # I'm leaving out upper-right as the timer in some of the sections prevents it from working
    # temporarily leaving out lr because oats
    stds = [ulStd, llStd, lrStd, middleStd]
    avgs = [ulAvg, llAvg, lrAvg, middleAvg]
    stdsNotMiddle = [ulStd, llStd, lrStd]
    avgsNotMiddle = [ulAvg, llAvg, lrAvg]

    doorTransition = True
    if current_state == STILL_IN_DOOR:
        if any(std > 11 for std in stdsNotMiddle) or any(avg > 11 for avg in avgsNotMiddle):
            doorTransition = False
    else:
        if any(std > 11.5 for std in stds) or any(avg > 11 for avg in avgs):
            doorTransition = False

    # cv2.imshow('ulBox', ulBox)
    # cv2.imshow('urBox', urBox)
    # cv2.imshow('llBox', llBox)
    # cv2.imshow('lrBox', lrBox)

    # gameplay_prev = previous_frame[60:-60, 60:-60].copy()

    # gray = cv2.cvtColor(gameplay_to_process, cv2.COLOR_BGR2GRAY)
    # gray_avg = round(np.average(gray))


    # gray_prev = cv2.cvtColor(gameplay_prev, cv2.COLOR_BGR2GRAY)
    # gray_avg_prev = round(np.average(gray_prev))
    doorState = NOT_IN_DOOR
    if doorTransition:
        if (current_state == STILL_IN_DOOR or current_state == ENTERING_DOOR):
            doorState = STILL_IN_DOOR
        if current_state == NOT_IN_DOOR:
            doorState = ENTERING_DOOR
    elif current_state == STILL_IN_DOOR and not doorTransition:
        doorState = EXITING_DOOR
    elif current_state == EXITING_DOOR:
        doorState = NOT_IN_DOOR
    else:
        #default to the current state
        doorState = current_state

    # in case I want to see what the gray avg is for debugging
    cv2.putText(gameplay_to_process, "Door State: " + str(doorState), (30, 80),
                  cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 1, cv2.LINE_AA)
    cv2.imshow('Process', gameplay_to_process)

    return doorState


if __name__ == '__main__':

    # input:
    # video URL
    processingStartTime = time.time()

    # videoFiles = ["vid1.mp4"]
    # videoFiles = ["vid1.mp4", "vid2.mp4"]
    # videoFiles = ["sloaters27_4227.mp4", "sloaters27_4231.mp4"]
    # videoFiles = ["Zoast-4046.mp4"]
    # videoFiles = ["Behemoth-4056.mp4"]
    # videoFiles = ["Oatsngoats-4146.mp4"]
    videoFiles = ["Oatsngoats-4146.mp4", "Zoast-4046.mp4", "Behemoth-4056.mp4"]

    # start times in seconds
    startMin = 11
    startTimes = [24 + startMin * 60, 2 + startMin * 60, 3 + startMin * 60]
    doorDetectionInfo = [-1, -1]

    # Rumble
    rumbleCrop = [(140, 0), (540, 380)]

    # Sloaters
    sloatersCrop = [(0, 30), (375, 380)]

    zoastCrop = [(135, 0), (540, 380)]
    beheCrop = [(150, 12), (540, 380)]
    oatsCrop = [(180, 0), (540, 360)]

    gameCropCoords = [oatsCrop, zoastCrop, beheCrop]

    roomsCompared = 0

    captures = []
    startFrames = [0] * len(videoFiles)
    # inRoomTransition = [False] * len(videoFiles)
    processVideo = [True] * len(videoFiles)
    lastRoomFrameEnd = [0] * len(videoFiles)
    lastRoomTimeStr = [""] * len(videoFiles)
    currentDoorState = [NOT_IN_DOOR] * len(videoFiles)
    firstFrame = [True] * len(videoFiles)
    capturedFrames = [None] * len(videoFiles)

    for videoFile in videoFiles:
        captures.append(cv2.VideoCapture(videoFile))

    fr = int(captures[0].get(cv2.CAP_PROP_FPS))
    for idx, capture in enumerate(captures):
        # if fr != int(capture.get(cv2.CAP_PROP_FPS)):
        #     print("All video files must have the same frame rate!  current frame rates are: "
        #               + str(fr) + "," + int(capture.get(cv2.CAP_PROP_FPS)))
        #     exit(1)
        print("FR: " + str(capture.get(cv2.CAP_PROP_FPS)))
        startFrames[idx] = startTimes[idx] * capture.get(cv2.CAP_PROP_FPS)
        capture.set(cv2.CAP_PROP_POS_FRAMES, startFrames[idx])
        lastRoomFrameEnd[idx] = startFrames[idx]

    outputFrameRate = fr
    output = cv2.VideoWriter('output.avi',
                             cv2.VideoWriter_fourcc('H', '2', '6', '4'),
                             outputFrameRate,
                             (400 * len(captures), 380))


    while (any(ele.isOpened() for ele in captures)) and roomsCompared < roomsToCompare:
        # loop through all the captures.  If a capture is in a door transition don't do any processing
        # if all captures are in a door transition then move on to the next room
        for idx in range(len(captures)):

            if not processVideo[idx]:
                continue

            cap = captures[idx]
            # if this capture is closed, then we hit the end of the video and don't do any processing on it
            if not cap.isOpened():
                continue

            ret, frame = cap.read()
            if not cap.isOpened():
                continue

            # resize to a standard size
            frame = cv2.resize(frame, (540, 380), fx=0, fy=0, interpolation=cv2.INTER_CUBIC)

            # trim the video to just the gameplay
            # gameplayPreResize = frame[0:, 140:]
            gameplayPreResize = frame[gameCropCoords[idx][0][1]:gameCropCoords[idx][1][1],
                                      gameCropCoords[idx][0][0]:gameCropCoords[idx][1][0]]

            # resize to consistent size so the door transition checks can be standardized
            gameplay = cv2.resize(gameplayPreResize, (400, 380), fx=0, fy=0, interpolation=cv2.INTER_CUBIC)

            currentFrame = int(cap.get(cv2.CAP_PROP_POS_FRAMES))

            if not firstFrame[idx]:
                currentDoorState[idx] = check_for_door_state(gameplay, capturedFrames[idx], currentDoorState[idx])
            else:
                firstFrame[idx] = False

            if currentDoorState[idx] == EXITING_DOOR:
                # calculate time
                roomFrames = (currentFrame - lastRoomFrameEnd[idx])
                seconds = int(roomFrames / fr)

                if seconds < 3:
                    currentDoorState[idx] = STILL_IN_DOOR

            if currentDoorState[idx] == ENTERING_DOOR:
                roomFrames = (currentFrame - lastRoomFrameEnd[idx])
                seconds = int(roomFrames / fr)
                frames = int(roomFrames) % fr
                lastRoomTimeStr[idx] = str(seconds) + "s " + str(frames) + "f"
                cv2.imshow('Door Transition ' + str(idx+1), gameplay)
                lastRoomFrameEnd[idx] = currentFrame
                processVideo[idx] = False



            cv2.putText(gameplay,
                        "Prev: " + lastRoomTimeStr[idx],
                        (0, 12),
                        font,
                        fontScale * .5,
                        color,
                        thickness,
                        cv2.LINE_AA)
            cv2.putText(gameplay,
                        videoFiles[idx],
                        (0, 350),
                        font,
                        fontScale * .5,
                        color,
                        thickness,
                        cv2.LINE_AA)

            # cv2.imshow('Run ' + str(idx+1), gameplay)
            capturedFrames[idx] = gameplay

        if not any(ele == True for ele in processVideo):
            for idx in range(len(processVideo)):
                processVideo[idx] = True

            roomsCompared += 1
            print("Compared room " + str(roomsCompared))

        composite = np.concatenate(capturedFrames, axis=1)
        cv2.imshow("Comparison", composite)
        output.write(composite)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # release the video capture objects
    for capture in captures:
        capture.release()
    output.release()

    # Closes all the windows currently opened.
    cv2.destroyAllWindows()

    processingEndTime = time.time()
    print("Finished processing "
          + str(roomsToCompare) + " in "
          + str(processingEndTime - processingStartTime)
          + " seconds.  See you next mission!")
