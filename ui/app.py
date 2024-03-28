# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'app.ui'
##
## Created by: Qt User Interface Compiler version 5.15.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(873, 618)
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.path_text = QLabel(self.centralwidget)
        self.path_text.setObjectName(u"path_text")
        self.path_text.setGeometry(QRect(10, 0, 21, 16))
        self.treeView = QTreeView(self.centralwidget)
        self.treeView.setObjectName(u"treeView")
        self.treeView.setGeometry(QRect(10, 30, 611, 541))
        self.folder_att = QTextEdit(self.centralwidget)
        self.folder_att.setObjectName(u"folder_att")
        self.folder_att.setGeometry(QRect(630, 30, 231, 541))
        self.lineEdit = QLineEdit(self.centralwidget)
        self.lineEdit.setObjectName(u"lineEdit")
        self.lineEdit.setGeometry(QRect(40, 0, 651, 21))
        self.disk_info = QPushButton(self.centralwidget)
        self.disk_info.setObjectName(u"disk_info")
        self.disk_info.setGeometry(QRect(700, 0, 161, 21))
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(MainWindow)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 873, 21))
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QStatusBar(MainWindow)
        self.statusbar.setObjectName(u"statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)

        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"MainWindow", None))
        self.path_text.setText(QCoreApplication.translate("MainWindow", u"Path", None))
        self.disk_info.setText(QCoreApplication.translate("MainWindow", u"Get Disk Information", None))
    # retranslateUi

