Super Metroid Video Comparison
==============================

Tool for compositing two Super Metroid videos on a room by room basis.

Resources
---------


Requirements
------------
* Python

Installation
------------


Usage
-----

In order to compare two videos, the two videos must meet these criteria:
1. They must visit the rooms in the exact same order
2. They must be (at least about) the same frame rate, trying to compare a 60fps video and a 30fps video won't work

### Download the videos
You can download the videos however you want.  This is easy if they're both your own videos (Twitch provides links for you to download them)

I've included a script that uses [twitch-dl](https://github.com/ihaunek/twitch-dl) to download other videos from Twitch.

### Configure the videos
In order to crop the videos, you need to supply two coordinates per video.  The top-left x,y coordinate of gameplay, and the bottom-right x,y coordinate.

You can use the findBoundingBox script run:
python
