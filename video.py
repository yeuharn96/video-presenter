from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QHBoxLayout, QVBoxLayout, QLabel, \
    QSlider, QStyle, QSizePolicy, QFileDialog, QDesktopWidget
import sys
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtMultimediaWidgets import QVideoWidget
from PyQt5.QtGui import QIcon, QPalette
from PyQt5.QtCore import Qt, QUrl
from monitors import monitor_areas
 
 
class VideoPlayer(QWidget):
    def __init__(self, handle_mediastate_changed, handle_position_changed, handle_duration_changed,
        handle_muted_changed, handle_volume_changed):
        super().__init__()

        self.video_path = ''
        self.handle_mediastate_changed = handle_mediastate_changed
        self.handle_position_changed = handle_position_changed
        self.handle_duration_changed = handle_duration_changed
        self.handle_muted_changed = handle_muted_changed
        self.handle_volume_changed = handle_volume_changed

        self.setGeometry(350, 100, 700, 500)
        # self.setWindowIcon(QIcon('player.png'))
 
        self.init_ui()

        # hide window border
        self.setWindowFlags(Qt.FramelessWindowHint)
 
        self.show()
 
 
    def init_ui(self):
        #create media player object
        self.mediaPlayer = QMediaPlayer(None, QMediaPlayer.VideoSurface, notifyInterval=100)
 
        #create videowidget object
        videowidget = QVideoWidget()
        videowidget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
 
        #create slider
        # self.slider = QSlider(Qt.Horizontal)
        # self.slider.setRange(0,0)
        # self.slider.sliderMoved.connect(self.set_position)
 
        vboxLayout = QVBoxLayout()
        vboxLayout.addWidget(videowidget)
        self.setLayout(vboxLayout)

        self.mediaPlayer.setVideoOutput(videowidget)
 
        #media player signals
 
        self.mediaPlayer.stateChanged.connect(lambda state: self.handle_mediastate_changed(state == QMediaPlayer.PlayingState))
        self.mediaPlayer.positionChanged.connect(self.handle_position_changed)
        self.mediaPlayer.durationChanged.connect(self.handle_duration_changed)
        self.mediaPlayer.mutedChanged.connect(self.handle_muted_changed)
        self.mediaPlayer.volumeChanged.connect(self.handle_volume_changed)
 
 
    def set_file(self, path):
        if path != '':
            self.video_path = path
            self.mediaPlayer.setMedia(QMediaContent(QUrl.fromLocalFile(path)))
 
 
    def play_video(self):
        print('play video', self.video_path)
        if len(self.video_path) == 0: return

        try:
            if self.mediaPlayer.state() == QMediaPlayer.PlayingState:
                self.mediaPlayer.pause()
            else:
                self.mediaPlayer.play()
        except:
            self.handle_errors()
    
    def stop_video(self):
        self.mediaPlayer.stop()
    
    def toggle_mute(self):
        is_muted = self.mediaPlayer.isMuted()
        self.mediaPlayer.setMuted(not is_muted)
    
    def volume(self):
        return self.mediaPlayer.volume()

    def set_volume(self, volume):
        self.mediaPlayer.setVolume(volume)

    # def mediastate_changed(self, state):
    #     if self.mediaPlayer.state() == QMediaPlayer.PlayingState:
    #         self.playBtn.setIcon(QIcon('icons/pause.png'))
    #     else:
    #         self.playBtn.setIcon(QIcon('icons/play.png'))
    # def position_changed(self, position):
    #     self.slider.setValue(position)
    # def duration_changed(self, duration):
    #     self.slider.setRange(0, duration)
 
 
    def set_video_position(self, position):
        self.mediaPlayer.setPosition(position)
 
 
    def handle_errors(self):
        self.playBtn.setEnabled(False)
        self.label.setText("Error: " + self.mediaPlayer.errorString())
 
 
 
# print('monitor_areas :>', monitor_areas())
 
# app = QApplication(sys.argv)
# monitor = QDesktopWidget().screenGeometry(0)
# print('QT monitor :>',monitor.x(), monitor.y(), monitor.width(),monitor.height())
# window = Window()
# sys.exit(app.exec_())