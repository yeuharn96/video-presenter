from PyQt5.QtWidgets import QDialog, QListWidget, QListWidgetItem, QPushButton, QDialogButtonBox, QLineEdit, QMessageBox
from PyQt5 import uic, QtCore
from setting import Profile

EDIT_PROFILE_UI_FILE = r'.\ui\edit_profile.ui'
MANAGE_PROFILE_UI_FILE = r'.\ui\manage_profile.ui'

# Popup dialog to edit profile name
class EditProfile(QDialog):
    def __init__(self):
        super(EditProfile, self).__init__()
        uic.loadUi(EDIT_PROFILE_UI_FILE, self)

        self.result = None
        self.line_edit = self.findChild(QLineEdit, 'lineEdit')
        self.button_box = self.findChild(QDialogButtonBox, 'buttonBox')

        self.setWindowFlags(self.windowFlags() & ~QtCore.Qt.WindowContextHelpButtonHint)

    def get_result(self, title='', text = ''):
        self.setWindowTitle(title)
        self.line_edit.setText(text)
        res = self.exec()

        if res == QDialog.Accepted:
            txt = self.line_edit.text()
            return txt



# Manage profile window
class ManageProfile(QDialog):
    def __init__(self):
        super(ManageProfile, self).__init__()
        uic.loadUi(MANAGE_PROFILE_UI_FILE, self)

        self.edit_profile = EditProfile()

        self.profile_list = self.findChild(QListWidget, 'listWidget')
        self.list_profiles()
        self.profile_list.itemDoubleClicked.connect(self.switch_profile)

        self.btn_new = self.findChild(QPushButton, 'btn_new')
        self.btn_edit = self.findChild(QPushButton, 'btn_edit')
        self.btn_delete = self.findChild(QPushButton, 'btn_delete')
        self.btn_new.clicked.connect(self.new)
        self.btn_edit.clicked.connect(self.edit)
        self.btn_delete.clicked.connect(self.delete)
        
        self.button_box = self.findChild(QDialogButtonBox, 'buttonBox')
        self.button_box.accepted.connect(self.switch_profile)

        self.setWindowFlags(self.windowFlags() & ~QtCore.Qt.WindowContextHelpButtonHint)

        # self.show()

    def list_profiles(self):
        self.profile_list.clear()
        for p in Profile.profiles:
            item = QListWidgetItem(p.name)
            item.setData(QtCore.Qt.UserRole, p.id)
            self.profile_list.addItem(item)
    
    def selected_profile(self):
        item = self.profile_list.currentItem()
        return item.text(), item.data(QtCore.Qt.UserRole)

    def highlight_current(self):
        item = next((i for i in self.profile_list.findItems(Profile.get_current().name, QtCore.Qt.MatchExactly)), None)
        if item is not None: self.profile_list.setCurrentItem(item)


    def new(self):
        name = self.edit_profile.get_result('Add New Profile')
        if name is not None:
            Profile.add_profile(name)
            self.list_profiles()

    def edit(self):
        if self.profile_list.currentItem() is None: 
            QMessageBox.information(self, 'No profile selected', 'Please select a profile.')
        else:
            name, id = self.selected_profile()
            new_name = self.edit_profile.get_result('Edit Profile Name', name)
            if new_name is not None:
                Profile.get_profile(id).name = new_name
                self.list_profiles()

    def delete(self):
        if self.profile_list.currentItem() is None: 
            QMessageBox.information(self, 'No profile selected', 'Please select a profile.')
        elif self.profile_list.count() <= 1:
            QMessageBox.critical(self, 'Unable to delete profile', 'Must have at least 1 profile in list.')
        else:
            confirm_delete = QMessageBox.question(self, 'Confirm delete profile', 'Confirm delete this profile? (Action cannot be undone)')
            if confirm_delete == QMessageBox.Yes:
                Profile.remove_profile(self.selected_profile()[1])
                self.list_profiles()

    def switch_profile(self):
        # print('switch')
        if self.profile_list.currentItem() is None: self.profile_list.setCurrentRow(0)
        Profile.set_current(self.selected_profile()[1])
        self.hide()
