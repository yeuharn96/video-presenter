from PyQt5.QtWidgets import (QApplication, QWidget, QMainWindow, QPushButton, QCheckBox, QSpinBox, QSlider, QLabel,
    QDoubleSpinBox, QListWidget, QListWidgetItem, QFileDialog, QMessageBox, QDesktopWidget, QMenuBar,
    QMenu, QAction, QStatusBar, QToolTip)
from PyQt5 import uic, QtCore
from PyQt5.QtCore import QTimer, QRect
import sys
import os
from PyQt5.QtGui import QIcon, QCursor
from video import VideoPlayer
from monitors import monitor_areas
from setting import Profile
from manage_profile import ManageProfile

# wrapper class for components to communicate
class EmitEvent:
    def __init__(self):
        self.events = dict()

    def emit_event(self, name, *args):
        if name not in self.events: return
        for event in self.events[name]: event(*args)

    def listen_event(self, name, handler):
        if name not in self.events: self.events[name] = [handler]
        else: self.events[name].append(handler)

    def clear_event(self, name):
        if name in self.events: del self.events[name]


class VidlistControl(EmitEvent):
    event_add_media = 'add_media'
    event_remove_media = 'remove_media'
    event_select_media = 'select_media'

    def __init__(self, findChild):
        super().__init__()
        self.vidlist = findChild(QListWidget, 'vidlist')
        self.vidlist_btn_add = findChild(QPushButton, 'vidlist_btn_add')
        self.vidlist_btn_delete = findChild(QPushButton, 'vidlist_btn_delete')
        self.vidlist_btn_select = findChild(QPushButton, 'vidlist_btn_select')

        self.vidlist.itemDoubleClicked.connect(self.vidlist_select_video)
        self.vidlist_btn_add.clicked.connect(self.vidlist_add_video)
        self.vidlist_btn_delete.clicked.connect(self.vidlist_delete_video)
        self.vidlist_btn_select.clicked.connect(self.vidlist_select_video)

    def vidlist_add_video(self):
        folder = os.environ['USERPROFILE'] + '\\Videos'
        fpath, _ = QFileDialog.getOpenFileName(None, 'Select a video', folder, 'All Files (*);;MP4 Files (*.mp4)', 'MP4 Files (*.mp4)')
        # print(fpath)
        if len(fpath) > 0:
            item = QListWidgetItem(os.path.basename(fpath))
            item.setData(QtCore.Qt.UserRole, fpath)
            self.vidlist.addItem(item)

            self.emit_event(VidlistControl.event_add_media, fpath)
            
            Profile.videos.append(fpath)
            if self.vidlist.count() == 1:
                self.vidlist.setCurrentRow(0)
                self.vidlist_select_video()
        # for i in range(self.vidlist.count()): print(self.vidlist.item(i).data(QtCore.Qt.UserRole))
    
    def vidlist_delete_video(self):
        video_idx = self.vidlist.currentRow()
        self.vidlist.takeItem(video_idx)

        self.emit_event(VidlistControl.event_remove_media, video_idx)
        
        del Profile.videos[video_idx]

    def vidlist_select_video(self):
        current_video = self.vidlist.currentItem()
        current_video_path = current_video.data(QtCore.Qt.UserRole)

        if current_video_path is None or len(current_video_path) == 0:
            QMessageBox.critical(self, 'Empty file path', 'If you sure the file exists, please consider remove and add the video file to list again.')
        elif not os.path.exists(current_video_path):
            QMessageBox.critical(self, 'File does not exist', f'Unable to find video file {current_video_path}')
        else:
            self.emit_event(VidlistControl.event_select_media, self.vidlist.currentRow())

class AudioControl(EmitEvent):
    event_volume_changed = 'volume_changed'
    event_toggle_mute = 'toggle_mute'

    def __init__(self, findChild):
        super().__init__()
        self.audio_sldr_volume = findChild(QSlider, 'audio_sldr_volume')
        self.audio_btn_mute = findChild(QPushButton, 'audio_btn_mute')
        self.audio_sb_volume = findChild(QSpinBox, 'audio_sb_volume')
        self.audio_btn_fadeout = findChild(QPushButton, 'audio_btn_fadeout')
        self.audio_sb_fadeout = findChild(QDoubleSpinBox, 'audio_sb_fadeout')

        self.audio_sldr_volume.valueChanged.connect(lambda volume: self.emit_event(AudioControl.event_volume_changed, volume))
        self.audio_btn_mute.clicked.connect(lambda: self.emit_event(AudioControl.event_toggle_mute))
        self.audio_sb_volume.editingFinished.connect(lambda: self.emit_event(AudioControl.event_volume_changed, self.audio_sb_volume.value()))
        self.audio_btn_fadeout.clicked.connect(self.audio_fadeout)
        self.audio_sb_fadeout.valueChanged.connect(self.audio_update_fadeout_second)
        self.audio_fadeout_increment = 0
        self.timer = QTimer()
        self.timer.timeout.connect(self.audio_fadeout)

    def audio_update_muted(self, muted):
        self.audio_btn_mute.setIcon(QIcon(f'icons/audio{"-mute" if muted else ""}.png'))

    def audio_update_volume(self, volume):
        self.audio_sldr_volume.setValue(volume)
        self.audio_sb_volume.setValue(volume)
        Profile.get_current().volume = volume

    def audio_update_fadeout_second(self, s):
        Profile.get_current().fadeout_second = s

    def audio_fadeout(self):
        fadeout_precision = 10 # in milliseconds

        volume = self.audio_sldr_volume.value()
        if not self.timer.isActive():
            self.fade_volume = volume
            second = round(self.audio_sb_fadeout.value() * 1000) # in milliseconds
            self.audio_fadeout_increment = volume / (second / fadeout_precision)
            self.timer.start(fadeout_precision)
        elif volume <= 0:
            self.timer.stop()
            return
        # print('fadeout', volume)
        self.fade_volume -= self.audio_fadeout_increment
        self.emit_event(AudioControl.event_volume_changed, round(self.fade_volume))

class PlaybackControl(EmitEvent):
    event_set_playback_loop = 'set_playback_loop'
    event_set_playback_next = 'set_playback_next'

    def __init__(self, findChild):
        super().__init__()
        CheckState = QtCore.Qt.CheckState
        self.playback_cb_loop = findChild(QCheckBox, 'playback_cb_loop')
        self.playback_cb_next = findChild(QCheckBox, 'playback_cb_next')
        self.playback_cb_loop.stateChanged.connect(self.playback_update_loop)
        self.playback_cb_next.stateChanged.connect(self.playback_update_next)
    
    def playback_update_loop(self, state):
        checked = state == QtCore.Qt.CheckState.Checked
        self.emit_event(PlaybackControl.event_set_playback_loop, checked)
        Profile.get_current().playback.loop = int(checked)

    def playback_update_next(self, state):
        checked = state == QtCore.Qt.CheckState.Checked
        self.emit_event(PlaybackControl.event_set_playback_next, checked)
        Profile.get_current().playback.next = int(checked)

class OutputControl(EmitEvent):
    event_show = 'show'
    event_hide = 'hide'
    event_apply_adjustment = 'apply_adjustment'

    def __init__(self, findChild):
        super().__init__()
        self.output_btn_show = findChild(QPushButton, 'output_btn_show')
        self.output_btn_hide = findChild(QPushButton, 'output_btn_hide')
        self.output_btn_fullscreen = findChild(QPushButton, 'output_btn_fullscreen')
        self.outputadj_sb_top = findChild(QSpinBox, 'outputadj_sb_top')
        self.outputadj_sb_left = findChild(QSpinBox, 'outputadj_sb_left')
        self.outputadj_sb_right = findChild(QSpinBox, 'outputadj_sb_right')
        self.outputadj_sb_bottom = findChild(QSpinBox, 'outputadj_sb_bottom')

        self.output_btn_show.clicked.connect(lambda: self.output_show(False))
        self.output_btn_hide.clicked.connect(lambda: self.emit_event(OutputControl.event_hide))
        self.output_btn_fullscreen.clicked.connect(lambda: self.output_show(True))
        self.outputadj_sb_top.valueChanged.connect(lambda value: self.outputadj_update_value('top', value))
        self.outputadj_sb_left.valueChanged.connect(lambda value: self.outputadj_update_value('left', value))
        self.outputadj_sb_right.valueChanged.connect(lambda value: self.outputadj_update_value('right', value))
        self.outputadj_sb_bottom.valueChanged.connect(lambda value: self.outputadj_update_value('bottom', value))
        self.outputadj_sb_top.editingFinished.connect(self.output_apply_adjustment)
        self.outputadj_sb_left.editingFinished.connect(self.output_apply_adjustment)
        self.outputadj_sb_right.editingFinished.connect(self.output_apply_adjustment)
        self.outputadj_sb_bottom.editingFinished.connect(self.output_apply_adjustment)

    def output_show(self, fullscreen=False):
        if not fullscreen: self.output_apply_adjustment()
        self.emit_event(OutputControl.event_show, fullscreen)
    
    def outputadj_update_value(self, pos, value):
        setattr(Profile.get_current().adjustment, pos, value)

    def output_apply_adjustment(self):
        mon = monitor_areas()
        # print(mon)
        if len(mon) == 1:
            x, y, w, h = mon[0]
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
        # print('calc2 >>',x,y,w,h, self.videoPlayer.frameGeometry().width(), self.videoPlayer.frameGeometry().height())

        self.emit_event(OutputControl.event_apply_adjustment, x, y, w, h)

class VideoControl(EmitEvent):
    event_play_video = 'play_video'
    event_stop_video = 'stop_video'
    event_set_video_position = 'set_video_position'
    event_skip_video_seconds = 'skip_video_seconds'
    event_next_video = 'next_video'

    def __init__(self, findChild):
        super().__init__()
        self.video_lbl_play_state = findChild(QLabel, 'video_lbl_play_state')
        self.video_lbl_current_video = findChild(QLabel, 'video_lbl_current_video')
        self.video_btn_play = findChild(QPushButton, 'video_btn_play')
        self.video_btn_stop = findChild(QPushButton, 'video_btn_stop')
        self.video_sldr = findChild(QSlider, 'video_sldr')
        self.video_lbl_current_time = findChild(QLabel, 'video_lbl_current_time')
        self.video_lbl_length = findChild(QLabel, 'video_lbl_length')
        self.video_sb_step = findChild(QSpinBox, 'video_sb_step')
        self.video_btn_backward = findChild(QPushButton, 'video_btn_backward')
        self.video_btn_forward = findChild(QPushButton, 'video_btn_forward')
        self.video_btn_prev = findChild(QPushButton, 'video_btn_prev')
        self.video_btn_next = findChild(QPushButton, 'video_btn_next')

        self.video_btn_play.setEnabled(False)
        self.video_btn_stop.setEnabled(False)
        self.video_btn_play.clicked.connect(lambda: self.emit_event(VideoControl.event_play_video))
        self.video_btn_stop.clicked.connect(lambda: self.emit_event(VideoControl.event_stop_video))
        self.video_sldr.sliderMoved.connect(self.video_sldr_moved)
        self.video_sb_step.valueChanged.connect(self.video_update_skip_step)
        self.video_btn_backward.clicked.connect(lambda: self.emit_event(VideoControl.event_skip_video_seconds, Profile.get_current().skip_step * -1))
        self.video_btn_forward.clicked.connect(lambda: self.emit_event(VideoControl.event_skip_video_seconds, Profile.get_current().skip_step))
        self.video_btn_prev.clicked.connect(lambda: self.emit_event(VideoControl.event_next_video, False))
        self.video_btn_next.clicked.connect(lambda: self.emit_event(VideoControl.event_next_video, True))
        self.video_duration = 0

    def handle_mediastate_changed(self, is_playing, is_stopped):
        if is_playing: self.video_lbl_play_state.setText('Now Playing:')
        elif is_stopped: self.video_lbl_play_state.setText('Stopped:')
        else: self.video_lbl_play_state.setText('Paused:')

        self.video_btn_play.setIcon(QIcon(f'icons/{"pause" if is_playing else "play"}.png'))
    
    def handle_video_position_changed(self, position):
        self.video_sldr.setValue(position)

        position = position // 1000
        self.video_lbl_current_time.setText(self._format_video_time(position))
        self.video_lbl_length.setText(self._format_video_lbl_length(position))

    def handle_video_duration_changed(self, duration):
        self.video_sldr.setRange(0, duration)

        duration = duration // 1000
        self.video_duration = duration
        self.video_lbl_length.setText(self._format_video_lbl_length(0))

    def video_sldr_moved(self, position):
        QToolTip.showText(QCursor.pos(), self._format_video_time(position // 1000))
        self.emit_event(VideoControl.event_set_video_position, position)

    def _format_video_time(self, time):
        hh = time // 3600
        mm = time % 3600 // 60
        ss = time % 60

        hh = f'{hh:02}:' if hh > 0 else ''
        return hh + f'{mm:02}:{ss:02}'

    def _format_video_lbl_length(self, position):
        return f'-{self._format_video_time(self.video_duration - position)}/{self._format_video_time(self.video_duration)}'

    def video_update_skip_step(self, value):
        Profile.get_current().skip_step = value
    
    def set_controls_enabled(self, enable):
        self.video_btn_play.setEnabled(enable)
        self.video_btn_stop.setEnabled(enable)

class MenuBarControl(EmitEvent):
    event_profile_changed = 'profile_changed'

    def __init__(self, findChild):
        super().__init__()
        self.manage_profile = ManageProfile()
        self.menu_profile_list = findChild(QMenu, 'menuSwitch_Profile')
        self.action_manage_profile = findChild(QAction, 'actionManage_Profile')
        self.menu_update_profile_list()
        self.action_manage_profile.triggered.connect(self.prompt_manage_profile)

        self.action_show_setting_folder = findChild(QAction, 'actionShow_Setting_Folder')
        self.action_show_setting_folder.triggered.connect(Profile.show_save_location)

    def prompt_manage_profile(self):
        self.manage_profile.highlight_current()
        self.manage_profile.exec()
        self.menu_update_profile_list()
        self.emit_event(MenuBarControl.event_profile_changed)

    def menu_update_profile_list(self):
        def _action_switch_profile(id):
            Profile.set_current(id)
            self.emit_event(MenuBarControl.event_profile_changed)

        self.menu_profile_list.clear()
        for row, p in enumerate(Profile.profiles, 1):
            act = self.menu_profile_list.addAction(f'{row}. {p.name}')
            act.setData(p.id)
            act.triggered.connect(lambda _, id=p.id: _action_switch_profile(id))


MAIN_UI_FILE = r'.\ui\main.ui'
class VideoPresenter(QMainWindow):
    def closeEvent(self, event):
        # print('closeEvent >>', event)
        Profile.save_all()
        sys.exit()
        
    def __init__(self):
        super(VideoPresenter, self).__init__()

        uic.loadUi(MAIN_UI_FILE, self)

        self.setWindowTitle("PyQt5 Media Player")
        # self.setWindowIcon(QIcon('player.png'))

        self.init_controls()

        self.load_profile_values()
        # load video path into playlist
        for vid_path in Profile.videos:
            item = QListWidgetItem(os.path.basename(vid_path))
            item.setData(QtCore.Qt.UserRole, vid_path)
            self.c_vidlist.vidlist.addItem(item)
            self.videoPlayer.add_media(vid_path)

        self.show()

    def init_controls(self):
        # window with media player object which will show on second screen 
        self.videoPlayer = VideoPlayer()
        self.videoPlayer.mediastate_changed.connect(lambda is_playing, is_stopped: self.c_video.handle_mediastate_changed(is_playing, is_stopped))
        self.videoPlayer.position_changed.connect(lambda position: self.c_video.handle_video_position_changed(position))
        self.videoPlayer.duration_changed.connect(lambda duration: self.c_video.handle_video_duration_changed(duration))
        self.videoPlayer.muted_changed.connect(lambda muted: self.c_audio.audio_update_muted(muted))
        self.videoPlayer.volume_changed.connect(lambda volume: self.c_audio.audio_update_volume(volume))
        self.videoPlayer.playlist_index_changed.connect(self.handle_playlist_index_changed)
        self.videoPlayer.hide_window.connect(self.handle_output_hide)

        # playlist
        self.c_vidlist = VidlistControl(self.findChild)
        self.c_vidlist.listen_event(VidlistControl.event_add_media, self.videoPlayer.add_media)
        self.c_vidlist.listen_event(VidlistControl.event_remove_media, self.videoPlayer.remove_media)
        self.c_vidlist.listen_event(VidlistControl.event_select_media, self.videoPlayer.select_media)

        # video seek bar, play/stop buttons, skip forward/backward, go to next/previous video
        self.c_video = VideoControl(self.findChild)
        self.c_video.listen_event(VideoControl.event_play_video, self.videoPlayer.play_video)
        self.c_video.listen_event(VideoControl.event_stop_video, self.videoPlayer.stop_video)
        self.c_video.listen_event(VideoControl.event_set_video_position, lambda position: self.videoPlayer.set_video_position(position))
        self.c_video.listen_event(VideoControl.event_skip_video_seconds, lambda seconds: self.videoPlayer.skip_video_seconds(seconds))
        self.c_video.listen_event(VideoControl.event_next_video, lambda is_next: self.videoPlayer.next_video(is_next))

        # set playback mode
        self.c_playback = PlaybackControl(self.findChild)
        self.c_playback.listen_event(PlaybackControl.event_set_playback_loop, self.videoPlayer.set_playback_loop)
        self.c_playback.listen_event(PlaybackControl.event_set_playback_next, self.videoPlayer.set_playback_next)

        # audio controls, mute, fadeout
        self.c_audio = AudioControl(self.findChild)
        self.c_audio.listen_event(AudioControl.event_toggle_mute, self.videoPlayer.toggle_mute)
        self.c_audio.listen_event(AudioControl.event_volume_changed, self.videoPlayer.set_volume)

        # buttons to show/hide self.videoPlayer window & position/size adjustments
        self.c_output = OutputControl(self.findChild)
        self.c_output.listen_event(OutputControl.event_show, self.handle_output_show)
        self.c_output.listen_event(OutputControl.event_hide, self.handle_output_hide)
        self.c_output.listen_event(OutputControl.event_apply_adjustment, lambda x, y, w, h: self.videoPlayer.setGeometry(x, y, w, h))

        # switch/manage profile, show setting file location
        self.c_menu_bar = MenuBarControl(self.findChild)
        self.c_menu_bar.listen_event(MenuBarControl.event_profile_changed, self.load_profile_values)
      
        # show current profile
        self.status_bar = self.findChild(QStatusBar, 'statusbar')
        self.status_lbl_profile = QLabel()
        self.status_bar.addPermanentWidget(self.status_lbl_profile)


    def load_profile_values(self):
        profile = Profile.get_current()
        self.status_lbl_profile.setText(f'Profile: {profile.name}') # status bar display

        # apply profile values
        self.c_output.outputadj_sb_top.setValue(profile.adjustment.top)
        self.c_output.outputadj_sb_bottom.setValue(profile.adjustment.bottom)
        self.c_output.outputadj_sb_left.setValue(profile.adjustment.left)
        self.c_output.outputadj_sb_right.setValue(profile.adjustment.right)
        self.c_output.output_apply_adjustment()

        self.c_audio.audio_sldr_volume.setValue(profile.volume)
        self.c_audio.audio_sb_volume.setValue(profile.volume)
        self.c_audio.audio_sb_fadeout.setValue(profile.fadeout_second)
        
        CheckState = QtCore.Qt.CheckState
        self.c_playback.playback_cb_loop.setCheckState(CheckState.Checked if profile.playback.loop == 1 else CheckState.Unchecked)
        self.c_playback.playback_cb_next.setCheckState(CheckState.Checked if profile.playback.next == 1 else CheckState.Unchecked)
        
        self.c_video.video_sb_step.setValue(profile.skip_step)

    # ============== EVENT HANDLERS ======================
    def handle_playlist_index_changed(self, idx):
        if idx > -1:
            self.c_vidlist.vidlist.setCurrentRow(idx)
            self.c_video.video_lbl_current_video.setText(self.c_vidlist.vidlist.currentItem().text())
    
    def handle_output_show(self, fullscreen = False):
        if fullscreen: self.videoPlayer.showFullScreen()
        else: self.videoPlayer.showNormal()
        self.c_video.set_controls_enabled(True)
    
    def handle_output_hide(self):
        if self.videoPlayer.isFullScreen():
            self.videoPlayer.showNormal()
        self.videoPlayer.hide()
        self.videoPlayer.mediaPlayer.pause()
        self.c_video.set_controls_enabled(False)
    # ============== EVENT HANDLERS END ==================
    


#==========================
# https://docs.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-showwindow
SW_HIDE = 0
SW_NORMAL = 1
SW_MAXIMIZE = 3
SW_MINIMIZE = 6
#==========================

if __name__ == '__main__':
    import ctypes

    print('Starting app...')
    app = QApplication(sys.argv)
    try:
        print('Loading settings...')
        Profile.load_all()
        Profile.set_current(0)
        print('Building windows...')
        window = VideoPresenter()
        # ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), SW_HIDE)
        # sys.exit(app.exec_())
        app.exec_()
    except Exception as e:
        w = QWidget()
        QMessageBox.critical(w, 'An unexpected error occurred', str(e))