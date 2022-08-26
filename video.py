from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QHBoxLayout, QVBoxLayout, QLabel, \
    QSlider, QStyle, QSizePolicy, QFileDialog, QDesktopWidget
import sys
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent, QMediaPlaylist
from PyQt5.QtMultimediaWidgets import QVideoWidget
from PyQt5.QtGui import QIcon, QPalette
from PyQt5.QtCore import Qt, QUrl, pyqtSignal, QFile, QIODevice, QByteArray, QBuffer
from monitors import monitor_areas
from setting import Profile
 
 
class VideoPlayer(QWidget):
    mediastate_changed = pyqtSignal(bool, bool)
    position_changed = pyqtSignal(int)
    duration_changed = pyqtSignal(int)
    muted_changed = pyqtSignal(bool)
    volume_changed = pyqtSignal(int)

    playlist_index_changed = pyqtSignal(int)

    def __init__(self):
        super().__init__()

        p = self.palette()
        p.setColor(self.backgroundRole(), Qt.black)
        self.setPalette(p)
        # self.setWindowIcon(QIcon('player.png'))
 
        self.init_ui()

        # hide window border
        self.setWindowFlags(Qt.FramelessWindowHint)
 
        # self.show()
 
 
    def init_ui(self):
        self.mediaPlayer = QMediaPlayer(None, QMediaPlayer.VideoSurface, notifyInterval=100)
        self.mediaPlayer.error.connect(self.handle_errors)
        
        self.playlist = QMediaPlaylist()
        self.playlist.setPlaybackMode(QMediaPlaylist.CurrentItemOnce)
        self.playlist.currentIndexChanged.connect(self.playlist_index_changed.emit)

        self.mediaPlayer.setPlaylist(self.playlist)
        self._playback_loop = False
        self._playback_next = False
 
        videowidget = QVideoWidget()
        videowidget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
 
        vboxLayout = QVBoxLayout()
        vboxLayout.addWidget(videowidget)
        vboxLayout.setContentsMargins(0,0,0,0)
        self.setLayout(vboxLayout)

        self.mediaPlayer.setVideoOutput(videowidget)
 
        #media player signals
        self.mediaPlayer.stateChanged.connect(lambda state: self.mediastate_changed.emit(state == QMediaPlayer.PlayingState, state == QMediaPlayer.StoppedState))
        self.mediaPlayer.positionChanged.connect(self.position_changed.emit)
        self.mediaPlayer.durationChanged.connect(self.duration_changed.emit)
        self.mediaPlayer.mutedChanged.connect(self.muted_changed.emit)
        self.mediaPlayer.volumeChanged.connect(self.volume_changed.emit)
 

    def add_media(self, path):
        if isinstance(path, str): path = [path]
        if not isinstance(path, list): return
        for p in path:
            self.playlist.addMedia(QMediaContent(QUrl.fromLocalFile(p)))
    
    def remove_media(self, idx):
        self.playlist.removeMedia(idx)
    
    def select_media(self, idx):
        self.playlist.setCurrentIndex(idx)
        # file = QFile(Profile.videos[0])
        # file.open(QIODevice.ReadOnly)
        # ba = QByteArray()
        # print(len(ba))
        # ba.append(file.readAll())
        # buffer = QBuffer()
        # buffer.setData(ba)
        # buffer.open(QIODevice.ReadOnly)
        # buffer.reset()
        # self.mediaPlayer.setMedia(QMediaContent(), buffer)
        # print(len(ba))

    def set_play_loop(self, loop):
        self._playback_loop = loop
        self._update_playback_mode()

    def set_play_next(self, next):
        self._playback_next = next
        self._update_playback_mode()

    def _update_playback_mode(self):
        mode = QMediaPlaylist.CurrentItemOnce
        if self._playback_loop and self._playback_next: 
            mode = QMediaPlaylist.Loop
        elif self._playback_loop: 
            mode = QMediaPlaylist.CurrentItemInLoop
        elif self._playback_next: 
            mode = QMediaPlaylist.Sequential

        self.playlist.setPlaybackMode(mode)

    def play_video(self):
        if self.playlist.mediaCount() == 0: return

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

 
    def set_video_position(self, position):
        self.mediaPlayer.setPosition(position)
 
 
    def handle_errors(self):
        print("Error: " + self.mediaPlayer.errorString())
 
 
 
# print('monitor_areas :>', monitor_areas())
 
# app = QApplication(sys.argv)
# monitor = QDesktopWidget().screenGeometry(0)
# print('QT monitor :>',monitor.x(), monitor.y(), monitor.width(),monitor.height())
# window = Window()
# sys.exit(app.exec_())