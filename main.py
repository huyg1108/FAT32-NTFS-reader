import sys
from PySide2 import QtWidgets
from psutil import disk_partitions
from ui import disk

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = disk.Ui_MainWindow()
        self.ui.setupUi(self)
        self.populate_disk_list()

    def populate_disk_list(self):
        disks = [partition.device for partition in disk_partitions(all=False)]
        self.ui.comboBox.clear()
        self.ui.comboBox.addItems(disks)

def main():
    app = QtWidgets.QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
