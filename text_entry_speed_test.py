#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
from PyQt5 import Qt, QtGui, QtCore, QtWidgets
import re
import text_input_technique as input_technique

class TextLogger(QtWidgets.QTextEdit):
    def __init__(self, example_text=""):
        super(TextLogger, self).__init__()
        self.setText(example_text)
        self.initUI()

    def initUI(self):
        self.setGeometry(0, 0, 400, 400)
        self.setWindowTitle('TextLogger')
        self.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.show()

    def keyPressEvent(self, ev):
        super(TextLogger, self).keyPressEvent(ev)
        #print("Pressed: " + ev.text())

    def keyReleaseEvent(self, ev):
        super(TextLogger, self).keyReleaseEvent(ev)
        #print("Released: " + ev.text())


def main():
    app = QtWidgets.QApplication(sys.argv)
    text_logger = TextLogger("Es war einmal ein Mann.")
    chord_input = input_technique.StandardInputMethod()
    text_logger.installEventFilter(chord_input)

    sys.exit(app.exec_())

if __name__ == '__main__':
    main()