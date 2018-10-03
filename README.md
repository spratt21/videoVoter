# vidPlayer.py
This file consists of three objects: a Login Window, A Player, and Vote Buttons.

The login window is designed to allow users to annotate the videos in multiple different sessions. When a user logs in, they use a unique user name which corresponds with the file which contains their previous annotations. 

The main object is the player. This contain a video player which diplays clips from a designated directory. It also has several controls for the video which can be individually added or removed from the configFile.

Finally the player contains Vote buttons. These are what the annotator uses to indicate what behavior is occuring in the video clip. These can be limited to exactly 1 vote per video or can allow for any number of votes.

# configFile
This allows the tool to be tailored to the needs of the lab. Specifically, (1) the path of the video clips, (2) the specification for potential behaviors, (3) keyboard shortcuts, and (4) what controls for the video are available to the user.
