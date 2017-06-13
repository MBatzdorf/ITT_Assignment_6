#!/usr/bin/python3

from PyQt5 import QtGui, QtWidgets, QtCore, uic
import sys


class TestDisplay(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.isFirstLetter = True
        self.timer = QtCore.QTime()
        self.initUI()

    def initUI(self):
        self.ui = uic.loadUi("text_entry_test.ui", self)
        self.textDisplay = self.ui.textToWrite
        self.textInputBox = self.ui.textInputBox.textChanged.connect(self.onTextChanged)
        self.show()

    def setTextDisplay(self, text):
        self.textDisplay.setText(text)

    def onTextChanged(self):
        if self.isFirstLetter:
            self.start_time_measurement()
            self.isFirstLetter = False
        else:
            current_input = self.sender().toPlainText()
            if current_input[-1] == '\n':
                self.stop_time_measurement()

            print(self.timer.elapsed())

    def start_time_measurement(self):
        self.timer.start()

    def stop_time_measurement(self):
        time_needed = self.timer.elapsed()
        print("Time needed: " + str(time_needed))
        # self.timer.


def main():
    app = QtWidgets.QApplication(sys.argv)
    test = TestDisplay()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
else:
    pass
