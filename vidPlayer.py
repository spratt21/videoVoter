#!/usr/bin/python
from PyQt5.QtCore import QDir, Qt, QUrl, QSize, QCoreApplication, pyqtSignal
from PyQt5.QtMultimedia import QMediaContent, QMediaPlayer
from PyQt5.QtMultimediaWidgets import QVideoWidget
from PyQt5.QtWidgets import (QApplication, QFileDialog, QHBoxLayout, QLabel, QSpacerItem, QMessageBox, QToolButton, QDoubleSpinBox,  
		QPushButton, QSizePolicy, QSlider, QStyle, QVBoxLayout, QWidget, QDialog, QInputDialog, QLineEdit, QComboBox)
from PyQt5.QtWidgets import QMainWindow,QWidget, QPushButton, QAction
from PyQt5.QtGui import QIcon, QKeySequence
from PyQt5 import QtNetwork
import sys
import random
import os
import configparser

# The Login Class create the window which pops up first and prompts the user to enter their USER_ID.
# It then uses this to create a csv unique to that ID where their future annotation will be stored
class Login(QDialog):
	def __init__(self):
		QDialog.__init__(self)

		self.finishedVids = set()
		self.csv = 0

		#Set Up Label Prompts, User Input Boxes and Submit buttons
		label1 = QLabel("If you have a User_ID, please enter below")
		label2 = QLabel("For new users, enter User_ID")
		self.Enter1 = QLineEdit()
		self.Enter2 = QLineEdit()
		self.loginButton = QPushButton("Login", self)
		self.newUserButton = QPushButton("Submit New ID", self)
		sp = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
		self.loginButton.setSizePolicy(sp)
		self.newUserButton.setSizePolicy(sp)
		self.loginButton.clicked.connect(self.loginOldUser)
		self.newUserButton.clicked.connect(self.submit)
		self.Enter1.returnPressed.connect(self.loginButton.setFocus)
		self.Enter2.returnPressed.connect(self.newUserButton.setFocus)

		#Label to inform user of error
		self.errorLabel = QLabel()
		self.errorLabel.setStyleSheet("font: 20pt; color: rgb(255, 0, 0)")

		#Format DialogBox and add widgets
		wid = QWidget(self)
		layout = QVBoxLayout()
		verticalSpacerSmall = QSpacerItem(10, 10, QSizePolicy.Fixed, QSizePolicy.Fixed)
		verticalSpacerLarge = QSpacerItem(10, 30, QSizePolicy.Fixed, QSizePolicy.Fixed)
		layout.addItem(verticalSpacerSmall)
		layout.addWidget(self.errorLabel)
		layout.addItem(verticalSpacerLarge)
		layout.addWidget(label1); layout.addWidget(self.Enter1); layout.addWidget(self.loginButton)
		layout.addItem(verticalSpacerLarge)
		layout.addWidget(label2); layout.addWidget(self.Enter2); layout.addWidget(self.newUserButton)
		layout.addItem(verticalSpacerSmall)
		layout.setAlignment(Qt.AlignTop)
		self.setLayout(layout)

		self.loginButton.setFocusPolicy(Qt.NoFocus)
		self.newUserButton.setFocusPolicy(Qt.NoFocus)

	def loadFinishedVideo(self, csv):
		for row in csv:
			self.finishedVids.add(row.split(".")[0])

	#reformats username and checks that there is no csv already of that name, then creare csv
	def submit(self):
		file = self.stripText(self.Enter2.text())
		csvFile = "./csvFiles/" + file + "_annotations.csv"
		if os.path.exists(csvFile):
			self.errorLabel.setText("That User_ID is taken, please select a different ID")
		else: 
			self.csv = open(csvFile, 'w+')
			self.close()

	#reformats username and opens csv of that name (if it exists)
	def loginOldUser(self):
		file = self.stripText(self.Enter1.text())
		csvFile = "./csvFiles/" + file + "_annotations.csv"
		if not os.path.exists(csvFile):
			self.errorLabel.setText("No User Exists with that ID")
		else: 
			self.csv = open(csvFile, 'r+')
			self.loadFinishedVideo(self.csv)
			self.close()

	def getCSV(self):
		return self.csv

	def getFinished(self):
		return self.finishedVids

	#reformats text
	def stripText(self, text):
		text = "".join(c for c in text if c not in ('!','.',':', ' ', ',', ';', '*'))
		text = text.lower()
		return text


# The VoteButton Class is a QPushButton which has be augmented to have a truth value associated with how many times
# it has been clicked (i.e. and "on" and "off"). The color of the button also changes depending on this value
class VoteButton(QPushButton):
	def __init__(self, parent=None):
		super(VoteButton, self).__init__(parent)
		self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
		self.setStyleSheet("background-color: rgb(255,150,150)")
		self.selected = False

	def select(self):
		if self.selected == True:
			self.selected = False
			self.setStyleSheet("background-color: rgb(255,150,150)")
		else: 
			self.selected = True
			self.setStyleSheet("background-color: rgb(180,255,150)")

	def getVal(self):
		return self.selected

	def reset(self):
		self.selected = False
		self.setStyleSheet("background-color: rgb(255,150,150)")



# This is my main object. It contains a media player (as well as a play/pause and restart button). It also has voteButtons
# and a Login window. The video is played and the user selects the buttons of the actions which occur. When they click "next" video,
# a confirmation video pops up with all the actions currently selected. If the user selects "yes", these are recorded in the csv file
# created in the Login class
class Player(QMainWindow):
	def __init__(self, playlist, parent=None):
		super(Player, self).__init__(parent)
		self.setWindowTitle("Behavior Voting System") 

		self.config = configparser.ConfigParser()
		self.config.read('configFile.cfg')
		self.voteOptions =  self.config['Epoch_Specs']['BUTTON_NAMES'].split(",")

		self.currVid = ""
		self.totalVids = len(os.listdir(self.config['Paths']['CLIP_PATH']))

		#Set Up Media Player
		self.mediaPlayer = QMediaPlayer(None, QMediaPlayer.VideoSurface)
		self.videoWidget = QVideoWidget()
		self.mediaPlayer.setVideoOutput(self.videoWidget)
		self.mediaPlayer.stateChanged.connect(self.mediaStateChanged)

		self.setUpButtons()
		self.setLayout()

		#Launch Login Window
		self.loginWindow = Login()
		self.loginWindow.resize(640,400)
		self.loginWindow.exec_()
		self.csv = self.loginWindow.getCSV()

		#set a default vote for one vote setting
		if self.config['Epoch_Specs']['ONE_VOTE_MAX'] == 'True':
			self.voteList[0].select()

		#Play First Video
		self.getVid()

	def toggleButton(self):
		s = self.sender()
		if self.config['Epoch_Specs']['ONE_VOTE_MAX'] == 'True':
			for vote in self.voteList:
					vote.reset()
		s.select()

	#Makes spaceBar do the same thing as clicking "Next Video"
	def keyPressEvent(self, e):
		if e.key() == QKeySequence(self.config['Keyboard_Shortcuts']['PLAY_SHORTCUT']):
			if self.config['Video_Control_Specs']['LEFT_RIGHT_BUTTONS'] == 'True':
				self.forwardFrame.setDown(False)
				self.backFrame.setDown(False)
			self.playVid()
		if e.key() == QKeySequence("Return"):
			self.speedSelect.clearFocus()
			self.mediaPlayer.setPlaybackRate(float(self.speedSelect.text()))

	def forward(self):
		self.mediaPlayer.pause()
		p = self.mediaPlayer.position()
		if p + 100 < self.mediaPlayer.duration():
			self.mediaPlayer.setPosition(p + 100)

	def back(self):
		self.mediaPlayer.pause()
		p = self.mediaPlayer.position()
		if p - 100 > 0:
			self.mediaPlayer.setPosition(p - 100)

	#Return string of selected action for current vid
	def getSelected(self):
		selected = " "
		comma = False
		for i in range(len(self.voteList)):
			if self.voteList[i].getVal():
				if comma:
					selected = selected + ", "
				selected = selected + self.voteOptions[i]
				comma = True
		if selected == " ":
			selected = "None"
		return selected

	#confirms selection, writes selection to csv, and then plays next video
	def next(self):
		if self.csv == 0:
			self.loginWindow.exec_()
			self.csv = self.loginWindow.getCSV()
			return 
		reply = 0
		msgBox = QMessageBox()
		msgBox.setText("Correct Action Labels?")
		s = self.getSelected()
		msgBox.setInformativeText(s + '\n')
		msgBox.setStandardButtons(QMessageBox.No | QMessageBox.Yes)
		msgBox.setDefaultButton(QMessageBox.Yes)
		msgBox.setStyleSheet("QLabel{min-width:600 px; font-size: 20px;} QPushButton{ width:250px; font-size: 18px; }");
		h = msgBox.exec_()
		if h == QMessageBox.No:
			return
		self.loginWindow.getFinished().add(self.currVid.split(".")[0])
		s = s.replace(" ","")
		s = s.replace("None","")
		self.csv.write(self.currVid + "," + s + "\n")
		for vote in self.voteList:
			vote.reset()
		if self.config['Epoch_Specs']['ONE_VOTE_MAX'] == 'True':
			self.voteList[0].select()
		self.getVid()

	#get and load random video
	def getVid(self):
		if len(self.loginWindow.getFinished()) == self.totalVids:
			msgBox = QMessageBox()
			msgBox.setText("Annotations Complete")
			msgBox.exec_()
			self.csv.close()
			self.csv = 0
			return
		self.currVid = random.choice(os.listdir(self.config['Paths']['CLIP_PATH']))
		while self.currVid in self.loginWindow.getFinished():
			self.currVid = random.choice(os.listdir(self.config['Paths']['CLIP_PATH']))
		self.path  = self.config['Paths']['CLIP_PATH'] + self.currVid
		self.mediaPlayer.setMedia(QMediaContent(QUrl.fromLocalFile(self.path)))
		self.mediaPlayer.play()
		self.setFocus()

	#play button 
	def playVid(self):
		self.mediaPlayer.setPlaybackRate(float(self.speedSelect.text()))
		if self.mediaPlayer.state() == QMediaPlayer.PlayingState:
			self.mediaPlayer.pause()
		else:
			self.mediaPlayer.play()

	#restart video
	def restart(self):
		if self.config['Video_Control_Specs']['LEFT_RIGHT_BUTTONS'] == 'True':
			self.forwardFrame.setDown(False)
			self.backFrame.setDown(False)
		self.mediaPlayer.setPlaybackRate(float(self.speedSelect.text()))
		self.setPosition(0)

	#change play/pause button based on state and restart video if video ends
	def mediaStateChanged(self, state):
		if self.mediaPlayer.state() == QMediaPlayer.PlayingState:
			self.playButton.setIcon(self.style().standardIcon(QStyle.SP_MediaPause))
			self.playButton.setText("PAUSE VIDEO (" + self.config['Keyboard_Shortcuts']['PLAY_SHORTCUT'] + ")")
		elif self.mediaPlayer.state() == QMediaPlayer.PausedState:
			self.playButton.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
			self.playButton.setText("PLAY VIDEO (" + self.config['Keyboard_Shortcuts']['PLAY_SHORTCUT'] + ")")
		else:
			self.mediaPlayer.setMedia(QMediaContent(QUrl.fromLocalFile(self.path)))
			self.mediaPlayer.pause()

	def positionChanged(self, position):
		self.positionSlider.setValue(position)

	def durationChanged(self, duration):
		self.positionSlider.setRange(0, duration)

	def setPosition(self, position):
		self.mediaPlayer.setPosition(position)

	def closeEvent(self, event):
		if self.csv != 0:
			self.csv.close()

	def setUpButtons(self):

		# Set Up Vote Buttons
		self.voteList = []
		shortcuts = self.config['Keyboard_Shortcuts']['VOTE_SHORTCUTS'].split(',')
		for i in range(len(self.voteOptions)):
			button = VoteButton(" " + self.voteOptions[i])
			button.clicked.connect(self.toggleButton)
			button.setShortcut(QKeySequence(str(shortcuts[i]).replace(" ", "")))
			button.setIconSize(QSize(35, 35))
			self.voteList.append(button)

		# Set Up Submit Button
		self.nextButton = QPushButton("SUBMIT ANNOTATIONS (" + self.config['Keyboard_Shortcuts']['SUBMIT_SHORTCUT'] + ")")
		self.nextButton.clicked.connect(self.next)
		self.nextButton.setShortcut(QKeySequence(self.config['Keyboard_Shortcuts']['SUBMIT_SHORTCUT']))
		self.nextButton.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)

		# Set Up Video Scroll Bar
		if self.config['Video_Control_Specs']['SCROLL_BAR'] == 'True':
			self.positionSlider = QSlider(Qt.Horizontal)
			self.positionSlider.setRange(0, 0)
			self.positionSlider.sliderMoved.connect(self.setPosition)
			self.mediaPlayer.positionChanged.connect(self.positionChanged)
			self.mediaPlayer.durationChanged.connect(self.durationChanged)

		# Set Up Play Button
		if self.config['Video_Control_Specs']['PLAY_BUTTON'] == 'True':
			self.playButton = QPushButton("PLAY VIDEO (" + self.config['Keyboard_Shortcuts']['PLAY_SHORTCUT'] + ")")
			self.playButton.clicked.connect(self.playVid)
			self.playButton.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)

		# Set Up Restart Video Button
		if self.config['Video_Control_Specs']['RESTART_BUTTON'] == 'True':
			self.restartButton = QPushButton("RESTART (" + self.config['Keyboard_Shortcuts']['RESTART_SHORTCUT'] + ")")
			self.restartButton.clicked.connect(self.restart)
			self.restartButton.setShortcut(QKeySequence(self.config['Keyboard_Shortcuts']['RESTART_SHORTCUT']))
			self.restartButton.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
			self.restartButton.setIcon(self.style().standardIcon(QStyle.SP_MediaSkipBackward))

		# Set Up Left Right Buttons
		if self.config['Video_Control_Specs']['LEFT_RIGHT_BUTTONS'] == 'True':
			self.backFrame = QPushButton()
			self.forwardFrame = QPushButton()
			self.backFrame.clicked.connect(self.back)
			self.forwardFrame.clicked.connect(self.forward)
			self.backFrame.setShortcut(QKeySequence(self.config['Keyboard_Shortcuts']['LEFT_SHORTCUT']))
			self.forwardFrame.setShortcut(QKeySequence(self.config['Keyboard_Shortcuts']['RIGHT_SHORTCUT']))
			self.backFrame.setIcon(QIcon("./icons/back.png"))
			self.forwardFrame.setIcon(QIcon("./icons/forward.png"))
			self.backFrame.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
			self.forwardFrame.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)

		#Set Up Speed Spin Box
		if self.config['Video_Control_Specs']['SPEED_CONTROL'] == 'True':
			self.speedButton = QLabel("Select Speed: ")
			self.speedSelect = QDoubleSpinBox()
			self.speedSelect.setValue(1.0)
			self.speedSelect.setSingleStep(0.1)
			self.speedSelect.setFocusPolicy(Qt.ClickFocus)


	def setLayout(self):
	#Set Layout
		verticalSpacerSmall = QSpacerItem(10, 10, QSizePolicy.Fixed, QSizePolicy.Fixed)
		verticalSpacerLarge = QSpacerItem(10, 200, QSizePolicy.Fixed, QSizePolicy.Fixed)
		voteBox = QHBoxLayout()
		voteWidget = QWidget(self)
		for i in range(len(self.voteOptions)):
			voteBox.addWidget(self.voteList[i])
		voteWidget.setLayout(voteBox)

		vidBox = QVBoxLayout()
		vidWidget = QWidget(self)
		vidBox.addWidget(self.videoWidget, 8)
		if self.config['Video_Control_Specs']['SCROLL_BAR'] == 'True':
			vidBox.addWidget(self.positionSlider, 1)
		vidBox.addWidget(voteWidget, 2)
		vidBox.addWidget(self.nextButton, 1)
		vidWidget.setLayout(vidBox)

		if self.config['Video_Control_Specs']['LEFT_RIGHT_BUTTONS'] == 'True':
			frameBox = QHBoxLayout()
			frameWidget = QWidget(self)
			frameBox.addWidget(self.backFrame)
			frameBox.addWidget(self.forwardFrame)
			frameWidget.setLayout(frameBox)

		if self.config['Video_Control_Specs']['SPEED_CONTROL'] == 'True':
			speedBox = QHBoxLayout()
			speedWidget = QWidget(self)
			speedBox.addWidget(self.speedButton)
			speedBox.addWidget(self.speedSelect)
			speedWidget.setLayout(speedBox)

		controlBox = QVBoxLayout()
		controlWidget = QWidget(self)
		controlBox.addWidget(self.playButton)
		if self.config['Video_Control_Specs']['LEFT_RIGHT_BUTTONS'] == 'True':
			controlBox.addWidget(frameWidget)
		controlBox.addWidget(self.restartButton)
		if self.config['Video_Control_Specs']['SPEED_CONTROL'] == 'True':
			controlBox.addWidget(speedWidget)
		controlBox.addItem(verticalSpacerLarge)
		controlWidget.setLayout(controlBox)

		wid = QWidget(self)
		self.setCentralWidget(wid)
		mainBox = QHBoxLayout()
		mainBox.addWidget(vidWidget, 4)
		mainBox.addWidget(controlWidget, 1)
		wid.setLayout(mainBox)

if __name__ == '__main__':
	if not os.path.isdir("./csvFiles"):
		os.mkdir("./csvFiles")
	if not os.path.isfile("./configFile.cfg"):
		print("Please set up config file")
	else:
		import sys
		app = QApplication(sys.argv)
		player = Player(sys.argv[1:])
		player.resize(1000, 700)
		player.show()
		sys.exit(app.exec_())

