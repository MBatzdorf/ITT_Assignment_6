#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
from PyQt5 import Qt, QtGui, QtCore, QtWidgets
import re

class TextLogger(QtWidgets.QTextEdit):
 
    def __init__(self, example_text=""):
        super(TextLogger, self).__init__()
        self.setText(example_text)
        self.initUI()
        
    def initUI(self):      
        self.setGeometry(0, 0, 400, 400)
        self.setWindowTitle('TextLogger')
        self.setFocusPolicy(QtCore.Qt.StrongFocus)
        #self.setMouseTracking(True)
        self.show()

    def keyPressEvent(self, ev):
        super(TextLogger, self).keyPressEvent(ev)
        print("Pressed: " + ev.text())
    
    def keyReleaseEvent(self, ev):
        super(TextLogger, self).keyReleaseEvent(ev)
        print("Released: " + ev.text())

class ChordInputMethod(QtCore.QObject):

    VALID_LETTERS="[a-zäöüß]"
    CHORDS = {frozenset(["a","s","d"]): "das",
             frozenset(["r","w"]): "Raphael Wimmer",
             }

    def __init__(self):
        super(ChordInputMethod, self).__init__()
        self.keys = []
        self.chords = ChordInputMethod.CHORDS

    def get_word(self):
        try:
            return self.chords[frozenset(self.keys)] + " "
        except KeyError:
            return "".join(self.keys)
        

    def eventFilter(self, watched_textedit, ev):
        if not ev.spontaneous():
            return False # ignore events that we injected ourselves
        if not ev.type() in [Qt.QKeyEvent.KeyPress, Qt.QKeyEvent.KeyRelease]:
            return False # ignore everything else
        if re.match(ChordInputMethod.VALID_LETTERS, ev.text().lower()) is None:
            return False # only check this _after_ we are sure that we have a QKeyEvent!
        # TODO: allow autorepeat when only a single key is pressed at the moment
        if ev.isAutoRepeat(): # completely eliminate these, as they might interfere with chords!
                return True
        # finally, we only have interesting key presses/releases left
        if ev.type() == Qt.QKeyEvent.KeyPress: # collect keys
            self.keys.append(ev.text())
            return True # always filter press events
        elif ev.type() == Qt.QKeyEvent.KeyRelease: # release chord once one of the keys is released
            if len(self.keys) > 0:
                result = self.get_word()
                Qt.qApp.postEvent(watched_textedit, QtGui.QKeyEvent(Qt.QKeyEvent.KeyPress, 0, QtCore.Qt.NoModifier, text = result))
                Qt.qApp.postEvent(watched_textedit, QtGui.QKeyEvent(Qt.QKeyEvent.KeyRelease, 0, QtCore.Qt.NoModifier, text = result))
                self.keys = []
            return True # also when non-printables are released (sensible?)
        else:
            print("Should'nt arrive here: " + str(ev))
            return False


def main():
    app = QtWidgets.QApplication(sys.argv)
    text_logger = TextLogger("Es war einmal ein Mann.")
    chord_input = ChordInputMethod()
    text_logger.installEventFilter(chord_input)

    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
