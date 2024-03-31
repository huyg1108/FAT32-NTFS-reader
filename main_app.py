import os
import sys
from PySide2 import QtWidgets, QtCore, QtGui
from psutil import disk_partitions
from typing import Union
from NTFS import *
from FAT32 import *
from ui import app, disk
import shutil
from send2trash import send2trash

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = disk.Ui_MainWindow()
        self.ui.setupUi(self)
        self.setWindowTitle("Volume Selection")
        self.populate_disk_list()
        self.ui.comboBox.activated[str].connect(self.drive_selected)
        self.folder_explorer = None
        self.setStyleSheet("QMainWindow { background-color: #CCCCCC; }")

        icon = QtGui.QIcon("icon/drive_icon.png")
        self.setWindowIcon(icon)

    def populate_disk_list(self):
        disks = [partition.device.rstrip("\\") for partition in disk_partitions(all=False)]
        self.ui.comboBox.clear()

        for disk in disks:
            icon = QtGui.QIcon("icon/drive_icon.png")
            self.ui.comboBox.addItem(icon, disk)

        font = QtGui.QFont("Arial", 10)
        self.ui.comboBox.setFont(font)

    def drive_selected(self, volume_name):
        volume_name = volume_name.rstrip("\\")
        volume = None
        if FAT32.check_fat32(volume_name):
            volume = FAT32(volume_name)
        elif NTFS.is_ntfs(volume_name):
            volume = NTFS(volume_name)

        if volume:
            # Kiểm tra nếu cửa sổ FolderExplorer đã được tạo trước đó
            if self.folder_explorer and self.folder_explorer.isVisible():
                self.folder_explorer.close()  # Đóng cửa sổ cũ nếu còn mở
            self.folder_explorer = FolderExplorer(volume, volume_name)
            self.folder_explorer.show()


class DriveInfoWindow(QtWidgets.QWidget):
    def __init__(self, drive_info: str):
        super().__init__()
        self.setWindowTitle("Drive Information")
        layout = QtWidgets.QVBoxLayout()
        self.info_label = QtWidgets.QLabel(drive_info)
        layout.addWidget(self.info_label)
        self.setLayout(layout)
        self.resize(400, 300)

        font = self.info_label.font()
        font.setPointSize(12)
        self.info_label.setFont(font)

        icon = QtGui.QIcon("icon/drive_icon.png")
        self.setWindowIcon(icon)


class TextFileContentWindow(QtWidgets.QWidget):
    def __init__(self, content: str, title):
        super().__init__()
        self.setWindowTitle(title)
        layout = QtWidgets.QVBoxLayout()
        self.content_textedit = QtWidgets.QTextEdit()
        self.content_textedit.setPlainText(content)
        layout.addWidget(self.content_textedit)
        self.setLayout(layout)
        self.resize(600, 400)

        font = self.content_textedit.font()
        font.setPointSize(12)
        self.content_textedit.setFont(font)

        icon = QtGui.QIcon("icon/text_icon.png")
        self.setWindowIcon(icon)


class FolderExplorer(app.Ui_MainWindow, QtWidgets.QMainWindow):
    def __init__(self, volume: Union[FAT32, NTFS], volume_name) -> None:
        super(FolderExplorer, self).__init__()
        self.setupUi(self)
        self.vol = volume
        self.vol_name = volume_name
        self.setWindowTitle(self.vol_name)
        self.populate()
        root_index = self.model.index(self.vol_name) 
        self.treeView.setRootIndex(root_index)

        icon = QtGui.QIcon("icon/file_icon.png")
        self.setWindowIcon(icon)

        # Interaction
        self.treeView.clicked.connect(self.show_folder_info)
        self.treeView.clicked.connect(self.show_path)
        self.treeView.doubleClicked.connect(self.show_txt_file_content)
        self.disk_info.clicked.connect(self.show_drive_info)

        # Context menu
        self.treeView.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.treeView.customContextMenuRequested.connect(self.show_context_menu)

        # Font for QTextEdit
        font = QtGui.QFont("Arial", 12)
        self.folder_att.setFont(font)

        self.setStyleSheet("QMainWindow { background-color: #CCCCCC; }")

    def populate(self):
        self.model = QtWidgets.QFileSystemModel()
        self.model.setRootPath(QtCore.QDir.rootPath())
        self.treeView.setModel(self.model)

    def show_folder_info(self):
        try:
            index = self.treeView.currentIndex()
            folder_path = self.model.filePath(index)
            
            self.vol.change_dir(folder_path)

            if check_path_type(folder_path) == 0:
                file = self.vol.get_folder_file_information(folder_path, 0)
            else:
                file = self.vol.get_folder_file_information(folder_path, 1)

            flag = file['Flags']
            atts = []

            if flag & 0b1:
                atts.append('Read-Only')
            if flag & 0b10:
                atts.append('Hidden')
            if flag & 0b100:
                atts.append('System')
            if flag & 0b1000:
                atts.append('Vollable')
            if flag & 0b10000:
                atts.append('Directory')
            if flag & 0b100000:
                atts.append('Archive')

            info_text = f"Name: {file['Name']}\n"
            if atts:
                info_text += f"Attribute: {', '.join(atts)}\n"
            else:
                info_text += "Attribute: None\n"
            info_text += f"Date Created: {str(file['Date Created'])}\n"
            info_text += f"Time Created: {str(file['Time Created'])}\n"
            info_text += f"Date Modified: {str(file['Date Modified'])}\n"
            info_text += f"Time Modified: {str(file['Time Modified'])}\n"
            if int(file['Bytes']) == 1:
                info_text += f"Total Size: {file['Bytes']} byte"
            else:
                info_text += f"Total Size: {file['Bytes']} bytes"

            self.folder_att.clear()
            self.folder_att.insertPlainText(info_text)
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error", str(e))

    def show_drive_info(self):
        try:
            drive_info = str(self.vol)
            self.drive_info_window = DriveInfoWindow(drive_info)
            self.drive_info_window.show()
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error", str(e))

    def show_path(self):
        try:
            index = self.treeView.currentIndex()
            folder_path = self.model.filePath(index)
            self.lineEdit.clear()
            self.lineEdit.setText(folder_path)

            font = self.lineEdit.font()
            font.setPointSize(10)
            self.lineEdit.setFont(font)
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error", str(e))

    def show_txt_file_content(self):
        try:
            index = self.treeView.currentIndex()
            file_path = self.model.filePath(index)

            if os.path.basename(file_path)[-4:] == '.txt':
                content = self.vol.get_text_content(file_path)
                self.text_file_content_window = TextFileContentWindow(content, os.path.basename(file_path))
                self.text_file_content_window.show()
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error", str(e))
    def move_to_recycle_bin(self, file_path):
        file_path = file_path.replace("/", "\\")
        send2trash(file_path)
    def restore_file_from_recycle_bin(self, file_path):
        pass
        
        
    def show_context_menu(self, pos):
        menu = QtWidgets.QMenu()
        delete_action = menu.addAction("Delete")
        action = menu.exec_(self.treeView.viewport().mapToGlobal(pos))
        if action == delete_action:
            try:
                print('Xoa')
                index = self.treeView.currentIndex()
                file_path = self.model.filePath(index)
                print(file_path)
                self.move_to_recycle_bin(file_path)
                print(file_path)
                self.populate()
                root_index = self.model.index(self.vol_name) 
                self.treeView.setRootIndex(root_index)
            except Exception as e:
                QtWidgets.QMessageBox.critical(self, "Error", str(e))


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec_())