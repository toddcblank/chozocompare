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
DOOR_CHECK_FRAMES = 5

NOT_STARTED = 0
ENTERING_DOOR = 1
STILL_IN_DOOR = 2
EXITING_DOOR = 3
NOT_IN_DOOR = 4
PROBABLY_IN_DOOR = 5
IN_DOOR_ENOUGH_FRAMES = PROBABLY_IN_DOOR + DOOR_CHECK_FRAMES

class Video:
    videoFilename = ""
    videoStartTime = 0
    gameplayCrop = [(0, 0), (540, 380)]
    videoTitle = ""


def check_for_pause(gameplay_to_process, video_id):

    topHud = gameplay_to_process[0:32, 0:150]
    # cv2.imshow("Hud", topHud)

    gray = cv2.cvtColor(topHud, cv2.COLOR_BGR2GRAY)
    # thresh = cv2.adaptiveThreshold(gray, 256, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 11, 2)
    ret, thresh = cv2.threshold(gray, 10, 256, cv2.THRESH_BINARY)
    threshAvg = 256 - np.average(thresh)

    # cv2.putText(thresh, str(threshAvg), (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 1, cv2.LINE_AA)
    # cv2.imshow("hud-thresh-" + video_id, thresh)

    return threshAvg > 245

def check_for_door_equalize(gameplay_to_process, current_state, video_id):

    gray = cv2.cvtColor(gameplay_to_process, cv2.COLOR_BGR2GRAY)
    # gray_avg = round(np.average(gray))

    thresh = cv2.adaptiveThreshold(gray, 256, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 9, 2)
    threshAvg = np.average(thresh)


    middleBox = thresh[50:-50, 50:-50].copy()
    middleAvg = np.average(middleBox)

    cv2.putText(thresh, str(threshAvg), (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,0,255), 1, cv2.LINE_AA)
    cv2.putText(middleBox, str(middleAvg), (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 1, cv2.LINE_AA)
    # cv2.imshow("thresh-" + video_id, thresh)
    # cv2.imshow("thresh-mb-" + video_id, middleBox)


    # doorTransition = check_for_door_avgStd(gameplay_to_process, current_state)
    doorTransition = (threshAvg > 235) and (current_state == STILL_IN_DOOR or middleAvg > 253)
    # if doorTransition and current_state == ENTERING_DOOR:
    #     currTime = time.time()
    #     cv2.imwrite("doors/" + video_id + "/door_in_" + str(currTime) + "-g.png", gameplay_to_process)
    #     cv2.imwrite("doors/" + video_id + "/door_in_" + str(currTime) + ".png", thresh)
    #     cv2.imwrite("doors/" + video_id + "/door_in_" + str(currTime) + "-m.png", middleBox)
    #
    # if not doorTransition and current_state == STILL_IN_DOOR:
    #     currTime = time.time()
    #     cv2.imwrite("doors/" + video_id + "/door_out_" + str(currTime) + "-g.png", gameplay_to_process)
    #     cv2.imwrite("doors/" + video_id + "/door_out_" + str(currTime) + ".png", thresh)
    #     cv2.imwrite("doors/" + video_id + "/door_out_" + str(currTime) + "-m.png", middleBox)

    return doorTransition

def check_for_door_fivePointAvgStd(gameplay_to_process, current_state):
    # grab the four corners of the screen, which should avoid doors, but include lots
    # of colors from normal rooms
    ulBox = gameplay_to_process[0:65, 0:120]
    llBox = gameplay_to_process[-65:, 0:120]
    # lrBox = gameplay_to_process[-100:, -180:]
    lrBox = gameplay_to_process[-65:-20, -120:]
    urBox = gameplay_to_process[0:65, -120:]
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

    return doorTransition

# Checks if we think we're in a door transition frame
# This currently naively checks if the middle part of the screen is dark.  So some rooms might be false positives
def check_for_door_state(video_frame, previous_frame, current_state, video_id=""):
    # cut out the hud of the gameplay
    gameplay_to_process = video_frame[32:, 0:].copy()
    doorTransition = check_for_door_equalize(gameplay_to_process, current_state, video_id)
    doorTransition = doorTransition and check_for_door_fivePointAvgStd(gameplay_to_process, current_state)

    if doorTransition:
        pause = check_for_pause(video_frame, video_id)
        # allow for a "pause" like screen on the title screen
        if pause and current_state != NOT_STARTED:
            doorTransition = False

    if doorTransition:
        if PROBABLY_IN_DOOR <= current_state < IN_DOOR_ENOUGH_FRAMES:
            doorState = current_state + 1
        elif current_state == IN_DOOR_ENOUGH_FRAMES:
            doorState = ENTERING_DOOR
        elif current_state == STILL_IN_DOOR or current_state == ENTERING_DOOR or current_state == EXITING_DOOR:
            doorState = STILL_IN_DOOR
        else:
            # cv2.imwrite("doors/door_" + str(time.time()) + "-c.png", video_frame)
            doorState = PROBABLY_IN_DOOR
    else:
        if current_state == STILL_IN_DOOR or current_state == ENTERING_DOOR:
            doorState = EXITING_DOOR
        elif current_state == EXITING_DOOR or current_state >= PROBABLY_IN_DOOR:
            doorState = NOT_IN_DOOR
        else:
            # default to the current state
            doorState = current_state

    # in case I want to see what the gray avg is for debugging
    # cv2.putText(gameplay_to_process, "Door State: " + str(doorState), (30, 80),
    #               cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 1, cv2.LINE_AA)
    # cv2.imshow('Process ' + video_id, gameplay_to_process)

    return doorState


def processVideoComparison(videos, startMin, roomsToCompare, outputFilename, showPreview):
    # input:
    # video URL
    processingStartTime = time.time()

    roomsCompared = 0
    gameCropCoords = []
    captures = []
    startTimes = []
    startFrames = [0] * len(videos)
    processVideo = [True] * len(videos)
    lastRoomFrameEnd = [0] * len(videos)
    lastRoomTimeStr = [""] * len(videos)
    currentDoorState = [NOT_STARTED] * len(videos)
    firstFrame = [True] * len(videos)
    capturedFrames = [None] * len(videos)

    for videoFile in videos:
        captures.append(cv2.VideoCapture(videoFile.videoFilename))
        gameCropCoords.append(videoFile.gameplayCrop)
        startTimes.append(videoFile.videoStartTime + startMin * 60)

    fr = int(captures[0].get(cv2.CAP_PROP_FPS))
    if fr < 58:
        DOOR_CHECK_FRAMES = 3
    else:
        DOOR_CHECK_FRAMES = 5
        
    for idx, capture in enumerate(captures):
        # All video files must have (at least about) the same frame rate!
        print("FR: " + str(capture.get(cv2.CAP_PROP_FPS)))
        startFrames[idx] = startTimes[idx] * capture.get(cv2.CAP_PROP_FPS)
        capture.set(cv2.CAP_PROP_POS_FRAMES, startFrames[idx])
        lastRoomFrameEnd[idx] = startFrames[idx]

    outputFrameRate = fr
    output = cv2.VideoWriter(outputFilename,
                             cv2.VideoWriter_fourcc(*'MP4V'),
                             outputFrameRate,
                             (256 * len(captures), 224))

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
            gameplay = cv2.resize(gameplayPreResize, (256, 224), fx=0, fy=0, interpolation=cv2.INTER_CUBIC)

            currentFrame = int(cap.get(cv2.CAP_PROP_POS_FRAMES))

            if not firstFrame[idx]:
                currentDoorState[idx] = check_for_door_state(gameplay, capturedFrames[idx], currentDoorState[idx], str(idx))
            else:
                firstFrame[idx] = False

            if currentDoorState[idx] == EXITING_DOOR:
                # calculate time
                roomFrames = (currentFrame - lastRoomFrameEnd[idx])
                seconds = roomFrames / fr

                if seconds < 1.2:
                    currentDoorState[idx] = STILL_IN_DOOR

            if currentDoorState[idx] == ENTERING_DOOR:
                roomFrames = (currentFrame - lastRoomFrameEnd[idx])
                seconds = int(roomFrames / fr)
                frames = int(roomFrames) % fr
                lastRoomTimeStr[idx] = str(seconds) + "s " + str(frames) + "f"
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
                        videos[idx].videoTitle,
                        (0, 200),
                        font,
                        fontScale * .5,
                        color,
                        thickness,
                        cv2.LINE_AA)

            capturedFrames[idx] = gameplay

        if not any(ele == True for ele in processVideo):
            for idx in range(len(processVideo)):
                processVideo[idx] = True

            roomsCompared += 1
            print("Compared room " + str(roomsCompared))

        composite = np.concatenate(capturedFrames, axis=1)
        if showPreview:
            cv2.imshow("Comparison (Press Q to stop)", composite)
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
