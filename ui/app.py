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
        MainWindow.resize(878, 632)
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.treeView = QTreeView(self.centralwidget)
        self.treeView.setObjectName(u"treeView")
        self.treeView.setGeometry(QRect(10, 40, 591, 531))
        self.folder_att = QTextEdit(self.centralwidget)
        self.folder_att.setObjectName(u"folder_att")
        self.folder_att.setGeometry(QRect(610, 40, 251, 531))
        self.lineEdit = QLineEdit(self.centralwidget)
        self.lineEdit.setObjectName(u"lineEdit")
        self.lineEdit.setEnabled(True)
        self.lineEdit.setGeometry(QRect(60, 10, 711, 21))
        self.disk_info = QPushButton(self.centralwidget)
        self.disk_info.setObjectName(u"disk_info")
        self.disk_info.setGeometry(QRect(660, 420, 161, 51))
        self.label = QLabel(self.centralwidget)
        self.label.setObjectName(u"label")
        self.label.setGeometry(QRect(0, 10, 61, 21))
        self.recycleBin = QPushButton(self.centralwidget)
        self.recycleBin.setObjectName(u"recycleBin")
        self.recycleBin.setGeometry(QRect(660, 490, 161, 51))
        self.refreshButton = QPushButton(self.centralwidget)
        self.refreshButton.setObjectName(u"refreshButton")
        self.refreshButton.setGeometry(QRect(780, 10, 71, 23))
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(MainWindow)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 878, 21))
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QStatusBar(MainWindow)
        self.statusbar.setObjectName(u"statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)

        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"MainWindow", None))
        self.disk_info.setText(QCoreApplication.translate("MainWindow", u"Get Volume Information", None))
        self.label.setText(QCoreApplication.translate("MainWindow", u"<html><head/><body><p align=\"center\"><span style=\" font-size:10pt;\">Path</span></p></body></html>", None))
        self.recycleBin.setText(QCoreApplication.translate("MainWindow", u"Recycle Bin", None))
        self.refreshButton.setText(QCoreApplication.translate("MainWindow", u"Refresh", None))
    # retranslateUi

