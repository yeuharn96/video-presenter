from PyQt5.QtWidgets import (QApplication, QMainWindow, QPushButton, QSpinBox, QSlider, QLabel,
    QDoubleSpinBox, QListWidget, QListWidgetItem, QFileDialog, QMessageBox, QDesktopWidget, QMenuBar,
    QMenu, QAction, QStatusBar)
from PyQt5 import uic, QtCore
from PyQt5.QtCore import QTimer, QRect
import sys
import os
from PyQt5.QtGui import QIcon
from video import VideoPlayer
from monitors import monitor_areas
from setting import Profile
from manage_profile import ManageProfile

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

        self.manage_profile = ManageProfile()


        self.vidlist = self.findChild(QListWidget, 'vidlist')
        self.vidlist_btn_add = self.findChild(QPushButton, 'vidlist_btn_add')
        self.vidlist_btn_delete = self.findChild(QPushButton, 'vidlist_btn_delete')
        self.vidlist_btn_select = self.findChild(QPushButton, 'vidlist_btn_select')

        for v in Profile.videos:
            item = QListWidgetItem(os.path.basename(v))
            item.setData(QtCore.Qt.UserRole, v)
            self.vidlist.addItem(item)

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
        self.audio_sb_fadeout.valueChanged.connect(self.audio_update_fadeout_second)
        self.audio_fadeout_increment = 0
        self.timer = QTimer()
        self.timer.timeout.connect(self.audio_fadeout)



        self.output_btn_show = self.findChild(QPushButton, 'output_btn_show')
        self.output_btn_hide = self.findChild(QPushButton, 'output_btn_hide')
        self.outputadj_sb_top = self.findChild(QSpinBox, 'outputadj_sb_top')
        self.outputadj_sb_left = self.findChild(QSpinBox, 'outputadj_sb_left')
        self.outputadj_sb_right = self.findChild(QSpinBox, 'outputadj_sb_right')
        self.outputadj_sb_bottom = self.findChild(QSpinBox, 'outputadj_sb_bottom')
        self.output_btn_show.clicked.connect(self.output_show)
        self.output_btn_hide.clicked.connect(self.videoPlayer.hide)
        self.outputadj_sb_top.valueChanged.connect(lambda value: self.outputadj_update_value('top', value))
        self.outputadj_sb_left.valueChanged.connect(lambda value: self.outputadj_update_value('left', value))
        self.outputadj_sb_right.valueChanged.connect(lambda value: self.outputadj_update_value('right', value))
        self.outputadj_sb_bottom.valueChanged.connect(lambda value: self.outputadj_update_value('bottom', value))
        self.outputadj_sb_top.editingFinished.connect(self.output_apply_adjustment)
        self.outputadj_sb_left.editingFinished.connect(self.output_apply_adjustment)
        self.outputadj_sb_right.editingFinished.connect(self.output_apply_adjustment)
        self.outputadj_sb_bottom.editingFinished.connect(self.output_apply_adjustment)



        self.menu_profile_list = self.findChild(QMenu, 'menuSwitch_Profile')
        self.action_manage_profile = self.findChild(QAction, 'actionManage_Profile')
        self.menu_update_profile_list()
        self.action_manage_profile.triggered.connect(self.prompt_manage_profile)

        self.status_bar = self.findChild(QStatusBar, 'statusbar')
        self.status_lbl_profile = QLabel()
        self.status_bar.addPermanentWidget(self.status_lbl_profile)
        self.status_update_current_profile()

        self.show()



    def vidlist_add_video(self):
        folder = os.environ['USERPROFILE'] + '\\Videos'
        fpath, _ = QFileDialog.getOpenFileName(self, 'Select a video', folder, 'All Files (*);;MP4 Files (*.mp4)', 'MP4 Files (*.mp4)')
        print(fpath)
        if len(fpath) > 0:
            item = QListWidgetItem(os.path.basename(fpath))
            item.setData(QtCore.Qt.UserRole, fpath)
            self.vidlist.addItem(item)
            Profile.videos.append(fpath)
            if self.vidlist.count() == 1:
                self.vidlist.setCurrentRow(0)
                self.vidlist_select_video()
        # for i in range(self.vidlist.count()): print(self.vidlist.item(i).data(QtCore.Qt.UserRole))
    
    def vidlist_delete_video(self):
        video_idx = self.vidlist.currentRow()
        self.vidlist.takeItem(video_idx)
        del Profile.videos[video_idx]

    def vidlist_select_video(self):
        current_video = self.vidlist.currentItem()
        current_video_path = current_video.data(QtCore.Qt.UserRole)

        if current_video_path is None or len(current_video_path) == 0:
            QMessageBox.critical(self, 'Empty file path', 'If you sure the file exists, please consider remove and add the video file to list again.')
        elif not os.path.exists(current_video_path):
            QMessageBox.critical(self, 'File does not exist', f'Unable to find video file {current_video_path}')
        else:
            self.videoPlayer.set_file(current_video_path)
            self.video_lbl_current_video.setText(current_video.text())

    # def _vidlist_add_videos(self, videos):
 

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
        Profile.get_current().volume = volume

    def audio_update_fadeout_second(self, s):
        Profile.get_current().fadeout_second = s

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



    def output_show(self):
        self.output_apply_adjustment()
        self.videoPlayer.show()

    def outputadj_update_value(self, pos, value):
        setattr(Profile.get_current().adjustment, pos, value)

    def output_apply_adjustment(self):
        mon = monitor_areas()
        # print(mon)
        if len(mon) == 1:
            x, y, w, h = mon[0]
        # elif int(self.setting['config'].get()) == 1:
        #     x, y, w, h = mon[0][2], mon[0][1], mon[0][2], mon[0][3]
        else:
            x, y, w, h = mon[1][0], mon[1][1], mon[1][2]-mon[1][0], mon[1][3]-mon[1][1]
        
        def parse_value(pos):
            try: return int(getattr(Profile.get_current().adjustment, pos))
            except: return 0
        # print('calc >>',x,y,w,h)
        y += parse_value('top')
        x += parse_value('left')
        w += parse_value('right') - parse_value('left')
        h += parse_value('bottom') - parse_value('top')
        # print('calc2 >>',x,y,w,h)

        # ag = QDesktopWidget().availableGeometry(self.videoPlayer)
        # print('ag >>', ag.contains(QRect(x,y,w,h)), ag)

        self.videoPlayer.setGeometry(x, y, w, h)
 
    def prompt_manage_profile(self):
        self.manage_profile.exec()
        self.menu_update_profile_list()
        self.status_update_current_profile()

    def menu_update_profile_list(self):
        def _action_switch_profile(id):
            Profile.set_current(id)
            self.status_update_current_profile()

        self.menu_profile_list.clear()
        for row, p in enumerate(Profile.profiles, 1):
            act = self.menu_profile_list.addAction(f'{row}. {p.name}')
            act.setData(p.id)
            act.triggered.connect(lambda _, id=p.id: _action_switch_profile(id))

    def status_update_current_profile(self):
        # print('main >>', Profile.get_current().name)
        profile = Profile.get_current()
        self.status_lbl_profile.setText(f'Profile: {profile.name}')
        # apply profile values
        self.outputadj_sb_top.setValue(profile.adjustment.top)
        self.outputadj_sb_bottom.setValue(profile.adjustment.bottom)
        self.outputadj_sb_left.setValue(profile.adjustment.left)
        self.outputadj_sb_right.setValue(profile.adjustment.right)
        self.audio_hsld_volume.setValue(profile.volume)
        self.audio_sb_fadeout.setValue(profile.fadeout_second)
        



    def closeEvent(self, event):
        # print('closeEvent >>', event)
        Profile.save_all()
        # self.videoPlayer.close()
        exit()

 
# print('monitor_areas :>', monitor_areas())
 
app = QApplication(sys.argv)
# monitor = QDesktopWidget().screenGeometry(0)
# print('QT monitor :>',monitor.x(), monitor.y(), monitor.width(),monitor.height())
Profile.load_all()
Profile.set_current(0)
window = VideoPresenter()
sys.exit(app.exec_())