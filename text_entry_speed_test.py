#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
from PyQt5 import Qt, QtGui, QtCore, QtWidgets
import re
import text_input_technique as input_technique

class TextLogger(QtWidgets.QTextEdit):

    SENTENCES = ["Es war einmal ein Mann.", "Der hatte einen Hut.", "Der Mann ging gerne spazieren!"]

    def __init__(self):
        super(TextLogger, self).__init__()
        self.elapsed = 0
        self.sentenceTimer = QtCore.QTime()
        self.wordTimer = QtCore.QTime()
        self.prepareNextTest()
        self.initUI()

    def initUI(self):
        self.setGeometry(0, 0, 400, 200)
        self.setWindowTitle('TextLogger')
        self.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.show()

    def prepareNextTest(self):
        if self.elapsed < len(self.SENTENCES):
            self.isFirstLetter = True
            self.setText("\n" + self.SENTENCES[self.elapsed])
            self.elapsed += 1
            self.stop_sentence_time_measurement()
            self.stop_word_time_measurement()
        else:
            sys.stderr.write("All trials done!")
            sys.exit(1)

    def keyPressEvent(self, ev):
        super(TextLogger, self).keyPressEvent(ev)
        if self.isFirstLetter:
            self.start_sentence_time_measurement()
            self.start_word_time_measurement()
            self.isFirstLetter = False

        if ev.key() == QtCore.Qt.Key_Space:
            wordTime = self.stop_word_time_measurement()
            self.logToStdOut(wordTime, False)
            self.start_word_time_measurement()

        if ev.key() == QtCore.Qt.Key_Return:
            wordTime = self.stop_word_time_measurement()
            sentenceTime = self.stop_sentence_time_measurement()
            self.logToStdOut(wordTime, False)
            self.logToStdOut(sentenceTime, True)
            self.prepareNextTest()

    def keyReleaseEvent(self, ev):
        super(TextLogger, self).keyReleaseEvent(ev)

    def start_sentence_time_measurement(self):
        self.sentenceTimer.start()

    def stop_sentence_time_measurement(self):
        time_needed = self.sentenceTimer.elapsed()
        return time_needed

    def start_word_time_measurement(self):
        self.wordTimer.start()

    def stop_word_time_measurement(self):
        time_needed = self.wordTimer.elapsed()
        return time_needed

    ''' TODO: This class should print a csv line to stdout
        Currently only debug information is printed
    '''
    def logToStdOut(self, time, done):
        if done:
            print("Time needed for sentence: " + str(time))
            return
        print("Time needed for word: " + str(time))

def main():
    app = QtWidgets.QApplication(sys.argv)
    text_logger = TextLogger()
    chord_input = input_technique.ChordInputMethod()
    text_logger.installEventFilter(chord_input)

    sys.exit(app.exec_())

if __name__ == '__main__':
    main()