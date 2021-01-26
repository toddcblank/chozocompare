import tkinter as tk
import cv2
from PIL import Image
from PIL import ImageTk
from tkinter import PhotoImage
import videoComparison
import configparser

config = configparser.ConfigParser()

class Video:
    videoFilename = "filename.mp4"
    videoStartTime = 0
    gameplayCrop = [(0, 0), (540, 380)]
    videoTitle = "Title"


def saveConfig(videos):

    config['video1'] = {
        'title': videos[0].videoTitle,
        'startTime': videos[0].videoStartTime,
        'gameplayCropUpperLeftX': videos[0].gameplayCrop[0][0],
        'gameplayCropUpperLeftY': videos[0].gameplayCrop[0][1],
        'gameplayCropLowerRightX': videos[0].gameplayCrop[1][0],
        'gameplayCropLowerRightY': videos[0].gameplayCrop[1][1],
        'filename': videos[0].videoFilename
    }
    config['video2'] = {
        'title': videos[1].videoTitle,
        'startTime': videos[1].videoStartTime,
        'gameplayCropUpperLeftX': videos[1].gameplayCrop[0][0],
        'gameplayCropUpperLeftY': videos[1].gameplayCrop[0][1],
        'gameplayCropLowerRightX': videos[1].gameplayCrop[1][0],
        'gameplayCropLowerRightY': videos[1].gameplayCrop[1][1],
        'filename': videos[1].videoFilename
    }

    with open('video-config.cfg', 'w') as configfile:
        config.write(configfile)

    return

def makeVideoForm(mainWin, videoIndex, video):

    entries = {}
    tk.Label(mainWin, text="Filename").grid(row=0, column=0  + 2 * videoIndex)
    filenameEntry1 = tk.Entry(mainWin)
    filenameEntry1.insert(0, video.videoFilename)
    filenameEntry1.grid(row=0, column=1 + 2 * videoIndex)
    entries["filename"] = filenameEntry1

    tk.Label(mainWin, text="Title").grid(row=1, column=0 + 2 * videoIndex)
    title_entry1 = tk.Entry(mainWin)
    title_entry1.insert(0, video.videoTitle)
    title_entry1.grid(row=1, column=1 + 2 * videoIndex)
    entries["title"] = title_entry1

    tk.Label(mainWin, text="Upper Left Gameplay").grid(row=2, column=0 + 2 * videoIndex)
    gpXY1 = tk.Entry(mainWin)
    gpXY1.insert(0, str(video.gameplayCrop[0][0]) + "," + str(video.gameplayCrop[0][1]))
    gpXY1.grid(row=2, column=1 + 2 * videoIndex)
    entries["topLeft"] = gpXY1

    tk.Label(mainWin, text="Lower Right Gameplay").grid(row=3, column=0 + 2 * videoIndex)
    gpXY2 = tk.Entry(mainWin)
    gpXY2.insert(0, str(video.gameplayCrop[1][0]) + "," + str(video.gameplayCrop[1][1]))
    gpXY2.grid(row=3, column=1 + 2 * videoIndex)
    entries["bottomRight"] = gpXY2

    tk.Label(mainWin, text="Start Screen Offset (s)").grid(row=4, column=0 + 2 * videoIndex)
    offset = tk.Entry(mainWin)
    offset.insert(0, video.videoStartTime)
    offset.grid(row=4, column=1 + 2 * videoIndex)
    entries["offset"] = offset

    filenameLoad1 = tk.Button(mainWin, text="Refresh Preview", command=(
        lambda e = entries: loadVideo(e, video)
    ))
    filenameLoad1.grid(row=6, column=1 + 2 * videoIndex)

    imageFrame = tk.Frame(mainWin, width=540, height=380)
    imageFrame.grid(row=7, column=0 + 2 * videoIndex, columnspan=2)

    imagePreview = tk.Label(imageFrame)
    imagePreview.grid(row=7, column=0 + 2 * videoIndex)

    entries["preview"] = imagePreview

    return entries

def makeCommonForm(mainWin, videos):
    tk.Label(mainWin, text="Video Start Time (in minutes)").grid(row=8, column=0, columnspan=2)
    timeStart = tk.Entry(mainWin)
    timeStart.insert(0, "0")
    timeStart.grid(row=8, column=3, columnspan=2)

    tk.Label(mainWin, text="Number of door transitions to process").grid(row=9, column=0, columnspan=2)
    doorTransitions = tk.Entry(mainWin)
    doorTransitions.insert(0, "999")
    doorTransitions.grid(row=9, column=3, columnspan=2)

    tk.Button(mainWin, text="                 Start               ",
              command=(
                  lambda: startComparison(videos, "output.mp4", True, timeStart, doorTransitions))
              ).grid(row=10, column=0, columnspan=6)
    return

class App:
    def __init__(self, window, window_title):
        photo = PhotoImage(file="rumble1Think.png")
        window.iconphoto(False, photo)
        self.window = window
        self.window.title(window_title)
        videos = [Video(), Video()]

        mainWin = self.window
        config.read('video-config.cfg')

        videos[0].videoTitle     = config['video1']['title']
        videos[0].videoStartTime = config['video1']['startTime']
        videos[0].gameplayCrop = [
            (int(config['video1']['gameplayCropUpperLeftX']), int(config['video1']['gameplayCropUpperLeftY'])),
            (int(config['video1']['gameplayCropLowerRightX']), int(config['video1']['gameplayCropLowerRightY'])),
        ]
        videos[0].videoFilename  = config['video1']['filename']

        videos[1].videoTitle     = config['video2']['title']
        videos[1].videoStartTime = config['video2']['startTime']
        videos[1].gameplayCrop   = [
            (int(config['video2']['gameplayCropUpperLeftX']), int(config['video2']['gameplayCropUpperLeftY'])),
            (int(config['video2']['gameplayCropLowerRightX']), int(config['video2']['gameplayCropLowerRightY'])),
        ]
        videos[1].videoFilename  = config['video2']['filename']

        makeVideoForm(mainWin, 0, videos[0])
        makeVideoForm(mainWin, 1, videos[1])
        makeCommonForm(mainWin, videos)
        self.window.mainloop()

def startComparison(videos, output, showPreview, startTimeEntry, doorComparisonsEntry):
    saveConfig(videos)
    startTime = int(startTimeEntry.get())
    doorComparisons = int(doorComparisonsEntry.get())
    videoComparison.processVideoComparison(videos, startTime, doorComparisons, output, showPreview)

def loadVideo(formFields, vid):
    vid.videoTitle = formFields["title"].get()
    vid.videoFilename = formFields["filename"].get()
    vid.videoStartTime = int(formFields["offset"].get())
    ulStr = formFields["topLeft"].get()
    vals = str.split(ulStr, ",")
    ul = (int(vals[0]),int(vals[1]))

    lrStr = formFields["bottomRight"].get()
    lrVals = str.split(lrStr, ",")
    lr = (int(lrVals[0]), int(lrVals[1]))
    vid.gameplayCrop = [ul, lr]

    cap = cv2.VideoCapture(vid.videoFilename)
    startFrames = vid.videoStartTime * cap.get(cv2.CAP_PROP_FPS)
    cap.set(cv2.CAP_PROP_POS_FRAMES, startFrames)
    ret, frame = cap.read()
    frame = cv2.resize(frame, (540, 380), fx=0, fy=0, interpolation=cv2.INTER_CUBIC)
    cv2.rectangle(frame, vid.gameplayCrop[0], vid.gameplayCrop[1], (0, 255, 0), 1)

    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGBA)
    img = Image.fromarray(frame)
    imgtk = ImageTk.PhotoImage(image=img)
    formFields["preview"].imgtk = imgtk
    formFields["preview"].configure(image=imgtk)


App(tk.Tk(), "Chozocompare")