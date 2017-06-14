#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
from PyQt5 import Qt, QtGui, QtCore, QtWidgets
import re


class StandardInputMethod(QtCore.QObject):
    VALID_LETTERS = "[a-zäöüß]"
    WORD_DELIMITER = QtCore.Qt.Key_Space
    SENTENCE_DELIMITER = QtCore.Qt.Key_Return

    def __init__(self):
        super(StandardInputMethod, self).__init__()
        self.currentWord = ""
        self.currentSentence = ""
        self.keys = []

    def get_word(self):
        return "".join(self.keys)

    def eventFilter(self, watched_textedit, ev):
        if not ev.spontaneous():
            return False  # ignore events that we injected ourselves
        if not ev.type() in [Qt.QKeyEvent.KeyPress, Qt.QKeyEvent.KeyRelease]:
            return False  # ignore everything else
        # if re.match(ChordInputMethod.VALID_LETTERS, ev.text().lower()) is None and ev.key() != self.WORD_DELIMITER
        # and ev.key() != self.SENTENCE_DELIMITER:
        #    return False # only check this _after_ we are sure that we have a QKeyEvent!
        if ev.isAutoRepeat():  # completely eliminate these!
            return True
        # finally, we only have interesting key presses/releases left
        if ev.type() == Qt.QKeyEvent.KeyPress:  # collect keys
            self.keys.append(ev.text())
            return True  # always filter press events
        elif ev.type() == Qt.QKeyEvent.KeyRelease:  # release chord once one of the keys is released
            if len(self.keys) > 0:
                result = self.get_word()
                Qt.qApp.postEvent(watched_textedit,
                                  QtGui.QKeyEvent(Qt.QKeyEvent.KeyPress, 0, QtCore.Qt.NoModifier, text=result))
                Qt.qApp.postEvent(watched_textedit,
                                  QtGui.QKeyEvent(Qt.QKeyEvent.KeyRelease, 0, QtCore.Qt.NoModifier, text=result))
                self.currentWord += result
                self.currentSentence += result
                self.keys = []
            if ev.key() == self.WORD_DELIMITER:
                Qt.qApp.postEvent(watched_textedit,
                                  QtGui.QKeyEvent(Qt.QKeyEvent.KeyPress, QtCore.Qt.Key_Space, QtCore.Qt.NoModifier,
                                                  text=" "))
                self.currentWord = []
            if ev.key() == self.SENTENCE_DELIMITER:
                Qt.qApp.postEvent(watched_textedit,
                                  QtGui.QKeyEvent(Qt.QKeyEvent.KeyPress, QtCore.Qt.Key_Return, QtCore.Qt.NoModifier,
                                                  text="\n"))
                self.currentWord = []
                self.currentSentence = []
            return True  # also when non-printables are released (sensible?)
        else:
            print("Should'nt arrive here: " + str(ev))
            return False


class ChordInputMethod(StandardInputMethod):
    CHORDS = {frozenset(["a", "s", "d"]): "das",
              frozenset(["w", "s", "a"]): "was",
              frozenset(["m", "a", "n"]): "Mann",
              frozenset(["l", "ä", "u", "f", "t"]): "läuft",
              frozenset(["s", "e"]): "es",
              frozenset(["w", "r", "a"]): "war",
              frozenset(["i", "e", "n"]): "ein",
              frozenset(["i", "c", "h"]): "ich",
              frozenset(["m", "g", "a"]): "mag",
              frozenset(["e", "d", "n"]): "den",
              frozenset(["i", "e", "s"]): "Eis",
              frozenset(["g", "e", "h"]): "Geh",
              frozenset(["n", "u"]): "nun",
              frozenset(["z", "u", "m"]): "zum",
              frozenset(["a", "u", "t", "o"]): "Auto",
              frozenset(["n", "i", "h", "c", "t"]): "nicht",
              frozenset(["s", "e", "h"]): "sehe",
              frozenset(["d", "i", "c", "h"]): "dich",
              frozenset(["w", "o"]): "wo",
              frozenset(["r", "e", "n", "s", "t"]): "rennst",
              frozenset(["d", "u"]): "du",
              frozenset(["h", "i", "n"]): "hin",
              frozenset(["d", "e", "r"]): "der",
              frozenset(["j", "u", "n", "g", "e"]): "Junge",
              frozenset(["w", "e", "i", "ß"]): "weiß",
              frozenset(["e", "r"]): "er",
              frozenset(["t", "u"]): "tut",
              frozenset(["r", "s", "i", "z", "e", "a", "p", "n"]): "spazieren",
              frozenset(["n", "i", "g"]): "ging",
              frozenset(["n", "i", "e"]): "nie",
              frozenset(["v", "i", "e", "l"]): "viele",
              frozenset(["l", "e", "t", "u"]): "Leute",
              frozenset(["m", "ö", "g", "e", "n"]): "mögen",
              frozenset(["d", "i", "c", "h"]): "dich",
              frozenset(["h", "u", "n", "d"]): "Hund",
              frozenset(["h", "a", "t"]): "hat",
              frozenset(["l", "i", "e", "b"]): "lieb",
              frozenset(["m", "e", "i", "n"]): "mein"
              }

    def __init__(self):
        super(ChordInputMethod, self).__init__()
        self.keys = []
        self.chords = ChordInputMethod.CHORDS

    def get_word(self):
        try:
            return self.chords[frozenset(self.keys)] + ""
        except KeyError:
            return "".join(self.keys)
