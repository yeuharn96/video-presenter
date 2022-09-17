import sys
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QSizePolicy
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent, QMediaPlaylist
from PyQt5.QtMultimediaWidgets import QVideoWidget
from PyQt5.QtCore import Qt, QUrl, pyqtSignal
 
 
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
 
        # media player signals
        self.mediaPlayer.stateChanged.connect(lambda state: self.mediastate_changed.emit(state == QMediaPlayer.PlayingState, state == QMediaPlayer.StoppedState))
        self.mediaPlayer.positionChanged.connect(self.position_changed.emit)
        self.mediaPlayer.durationChanged.connect(self.duration_changed.emit)
        self.mediaPlayer.mutedChanged.connect(self.muted_changed.emit)
        self.mediaPlayer.volumeChanged.connect(self.volume_changed.emit)
 

    # ==================== Playlist ====================
    def add_media(self, path):
        if isinstance(path, str): path = [path]
        if not isinstance(path, list): return
        for p in path:
            self.playlist.addMedia(QMediaContent(QUrl.fromLocalFile(p)))
    
    def remove_media(self, idx):
        self.playlist.removeMedia(idx)
    
    def select_media(self, idx):
        self.playlist.setCurrentIndex(idx)

    def set_playback_loop(self, loop):
        self._playback_loop = loop
        self._update_playback_mode()

    def set_playback_next(self, _next):
        self._playback_next = _next
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
    # ================ Playlist END ====================


    # ==================== Video ====================
    def play_video(self):
        if self.playlist.mediaCount() == 0: return

        if self.mediaPlayer.state() == QMediaPlayer.PlayingState:
            self.mediaPlayer.pause()
        else:
            self.mediaPlayer.play()
    
    def stop_video(self):
        self.mediaPlayer.stop()
    
    def set_video_position(self, position):
        self.mediaPlayer.setPosition(position)
 
    def skip_video_seconds(self, seconds):
        skip_to_position = self.mediaPlayer.position() + (seconds * 1000)
        self.mediaPlayer.setPosition(skip_to_position)
    
    def next_video(self, is_next=True):
        idx = self.playlist.nextIndex() if is_next else self.playlist.previousIndex()
        if idx > -1: self.playlist.setCurrentIndex(idx)
    # ==================== Video END ================

    
    # ==================== Audio ====================
    def toggle_mute(self):
        is_muted = self.mediaPlayer.isMuted()
        self.mediaPlayer.setMuted(not is_muted)
    
    def set_volume(self, volume):
        self.mediaPlayer.setVolume(volume)
    # ==================== Audio END ================


    def handle_errors(self):
        w = QWidget()
        QMessageBox.critical(w, 'Media player error', self.mediaPlayer.errorString())
        # print("Error: " + self.mediaPlayer.errorString())
 