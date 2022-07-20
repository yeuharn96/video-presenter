from PyQt5.QtWidgets import (QApplication, QMainWindow, QPushButton, QSpinBox, QSlider, QLabel,
    QDoubleSpinBox, QListWidget, QListWidgetItem, QFileDialog, QMessageBox)
from PyQt5 import uic, QtCore
from PyQt5.QtCore import QTimer
import sys
import os
from PyQt5.QtGui import QIcon
from video import VideoPlayer
from monitors import monitor_areas

# class VideoControl:
#     def __init__(self, findControl):

def format_video_time(time):
    hh = round(time / 3600)
    mm = round(time / 60 % 60)
    ss = round(time % 60)

    hh = f'{hh:02}:' if hh > 0 else ''
    return hh + f'{mm:02}:{ss:02}'


class VideoPresenter(QMainWindow):
    def __init__(self):
        super(VideoPresenter, self).__init__()
 
        uic.loadUi('main.ui', self)

        self.setWindowTitle("PyQt5 Media Player")
        # self.setWindowIcon(QIcon('player.png'))
        self.videoPlayer = VideoPlayer(
            handle_mediastate_changed = self.video_update_btn_play,
            handle_position_changed = self.video_update_current_position,
            handle_duration_changed = self.video_update_duration,
            handle_muted_changed = self.audio_update_muted,
            handle_volume_changed = self.audio_update_volume
        )

        self.timer = QTimer()
        self.timer.timeout.connect(self.audio_fadeout)


        self.vidlist = self.findChild(QListWidget, 'vidlist')
        self.vidlist_btn_add = self.findChild(QPushButton, 'vidlist_btn_add')
        self.vidlist_btn_delete = self.findChild(QPushButton, 'vidlist_btn_delete')
        self.vidlist_btn_select = self.findChild(QPushButton, 'vidlist_btn_select')

        self.vidlist_btn_add.clicked.connect(self.vidlist_add_video)
        self.vidlist_btn_delete.clicked.connect(self.vidlist_delete_video)
        self.vidlist_btn_select.clicked.connect(self.vidlist_select_video)



        self.video_lbl_current_video = self.findChild(QLabel, 'video_lbl_current_video')
        self.video_btn_play = self.findChild(QPushButton, 'video_btn_play')
        self.video_btn_stop = self.findChild(QPushButton, 'video_btn_stop')
        self.video_hsld = self.findChild(QSlider, 'video_hsld')
        self.video_lbl_current_time = self.findChild(QLabel, 'video_lbl_current_time')
        self.video_lbl_length = self.findChild(QLabel, 'video_lbl_length')

        self.video_btn_play.clicked.connect(self.videoPlayer.play_video)
        self.video_btn_stop.clicked.connect(self.videoPlayer.stop_video)
        self.video_hsld.sliderMoved.connect(self.videoPlayer.set_video_position)
        self.video_duration = 0



        self.audio_hsld_volume = self.findChild(QSlider, 'audio_hsld_volume')
        self.audio_btn_mute = self.findChild(QPushButton, 'audio_btn_mute')
        self.audio_lbl_volume = self.findChild(QLabel, 'audio_lbl_volume')
        self.audio_btn_fadeout = self.findChild(QPushButton, 'audio_btn_fadeout')
        self.audio_sb_fadeout = self.findChild(QDoubleSpinBox, 'audio_sb_fadeout')

        self.audio_btn_mute.clicked.connect(self.videoPlayer.toggle_mute)
        self.audio_hsld_volume.valueChanged.connect(self.videoPlayer.set_volume)
        self.audio_btn_fadeout.clicked.connect(self.audio_fadeout)
        self.audio_fadeout_increment = 0



        self.output_btn_show = self.findChild(QPushButton, 'output_btn_show')
        self.output_btn_hide = self.findChild(QPushButton, 'output_btn_hide')
        self.outputadj_sb_top = self.findChild(QSpinBox, 'outputadj_sb_top')
        self.outputadj_sb_left = self.findChild(QSpinBox, 'outputadj_sb_left')
        self.outputadj_sb_right = self.findChild(QSpinBox, 'outputadj_sb_right')
        self.outputadj_sb_bottom = self.findChild(QSpinBox, 'outputadj_sb_bottom')

        self.output_btn_show.clicked.connect(self.videoPlayer.show)
        self.output_btn_hide.clicked.connect(self.videoPlayer.hide)


        self.show()

    def vidlist_add_video(self):
        folder = os.environ['USERPROFILE'] + '\\Videos'
        fname, _ = QFileDialog.getOpenFileName(self, 'Select a video', folder, 'All Files (*);;MP4 Files (*.mp4)', 'MP4 Files (*.mp4)')
        print(fname)
        if len(fname) > 0:
            item = QListWidgetItem(os.path.basename(fname))
            item.setData(QtCore.Qt.UserRole, fname)
            self.vidlist.addItem(item)
            if self.vidlist.count() == 1:
                self.vidlist.setCurrentRow(0)
                self.vidlist_select_video()
        # for i in range(self.vidlist.count()): print(self.vidlist.item(i).data(QtCore.Qt.UserRole))
    
    def vidlist_delete_video(self):
        video_idx = self.vidlist.currentRow()
        self.vidlist.takeItem(video_idx)

    def vidlist_select_video(self):
        video_idx = self.vidlist.currentRow()
        current_video = self.vidlist.item(video_idx)
        current_video_path = current_video.data(QtCore.Qt.UserRole)

        if current_video_path is None or len(current_video_path) == 0:
            QMessageBox.critical(self, 'Empty file path', 'Please remove and add the video file to the list again.')
        elif not os.path.exists(current_video_path):
            QMessageBox.critical(self, 'File does not exist', f'Unable to find video file {current_video_path}')
        else:
            self.videoPlayer.set_file(current_video_path)
            self.video_lbl_current_video.setText(current_video.text())

 
    def video_update_btn_play(self, is_playing):
        self.video_btn_play.setIcon(QIcon(f'icons/{"pause" if is_playing else "play"}.png'))
        
    def video_update_current_position(self, position):
        self.video_hsld.setValue(position)

        position = position // 1000
        self.video_lbl_current_time.setText(format_video_time(position))
        self.video_lbl_length.setText(self._format_video_lbl_length(position))

    def video_update_duration(self, duration):
        self.video_hsld.setRange(0, duration)

        duration = duration // 1000
        self.video_duration = duration
        self.video_lbl_length.setText(self._format_video_lbl_length(0))

    def _format_video_lbl_length(self, position):
        return f'-{format_video_time(self.video_duration - position)}/{format_video_time(self.video_duration)}'

    def audio_update_muted(self, muted):
        self.audio_btn_mute.setIcon(QIcon(f'icons/audio{"-mute" if muted else ""}.png'))

    def audio_update_volume(self, volume):
        self.audio_hsld_volume.setValue(volume)
        self.audio_lbl_volume.setText(f'{volume}%')

    def audio_fadeout(self):
        fadeout_precision = 10 # in milliseconds
        
        volume = self.videoPlayer.volume()
        if not self.timer.isActive():
            second = round(self.audio_sb_fadeout.value() * 1000) # in milliseconds
            self.audio_fadeout_increment = volume / (second / fadeout_precision)
            self.timer.start(fadeout_precision)
        elif volume == 0:
            self.timer.stop()
            return
        # print('fadeout', volume)
        volume = max(0, volume - self.audio_fadeout_increment)
        self.videoPlayer.set_volume(round(volume))

 
    def closeEvent(self, event):
        print('closeEvent >>', event)
        self.videoPlayer.close()

 
print('monitor_areas :>', monitor_areas())
 
app = QApplication(sys.argv)
# monitor = QDesktopWidget().screenGeometry(0)
# print('QT monitor :>',monitor.x(), monitor.y(), monitor.width(),monitor.height())
window = VideoPresenter()
sys.exit(app.exec_())