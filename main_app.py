from PySide2 import QtWidgets, QtCore, QtGui
import os
import sys
from typing import Union
from NTFS import *
from FAT32 import *
from ui import app

class FolderExplorer(app.Ui_MainWindow, QtWidgets.QMainWindow):
    def __init__(self, volume: Union[FAT32, NTFS]) -> None:
        super(FolderExplorer, self).__init__()
        self.setupUi(self)
        self.vol = volume
        self.populate()
        root_index = self.model.index(volume_name) 
        self.treeView.setRootIndex(root_index)

        # Interaction
        self.treeView.clicked.connect(self.show_folder_info)
        self.treeView.clicked.connect(self.show_path)
        self.disk_info.clicked.connect(self.show_drive_info)

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
            info_text += f"Date Modified: {str(file['Date Modified'])}\n"
            info_text += f"Total Size: {file['Sector']} sector"

            self.folder_att.clear()
            self.folder_att.insertPlainText(info_text)
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error", str(e))

    def show_drive_info(self):
        # print in new window
        print(self.vol)

    def show_path(self):
        try:
            index = self.treeView.currentIndex()
            folder_path = self.model.filePath(index)
            self.lineEdit.clear()
            self.lineEdit.setText(folder_path)
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error", str(e))

if __name__ == "__main__":
    application = QtWidgets.QApplication(sys.argv)

    volume_name = 'E:'
    if FAT32.check_fat32(volume_name):
        vol = FAT32(volume_name)
    elif NTFS.is_ntfs(volume_name):
        vol = NTFS(volume_name)

    window = FolderExplorer(vol)
    window.show()
    sys.exit(application.exec_())