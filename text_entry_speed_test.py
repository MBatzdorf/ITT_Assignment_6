#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import configparser
from PyQt5 import Qt, QtGui, QtCore, QtWidgets
import re
import numpy
from random import randint
import time
import text_input_technique as input_technique


class TextLogger(QtWidgets.QTextEdit):
    SHORT_SENTENCES = ["Wo rennst du hin.", "Ich sehe dich nicht.", "Es war ein Mann.", "Ich mag das Eis.",
                       "Geh nun zum Auto.", "Der hat einen Hut.", "Es ist heiß hier.", "Das Spiel ist gut!",
                       "Wir essen zu viel!", "Schieß ein Tor!"]
    LONG_SENTENCES = ["Der Mann ging nie spazieren", "Mein Hund hat dich lieb", "Viele Leute mögen dich.",
                      "Der Junge weiß nicht was er tut", "Ich hab den Termin verpasst.", "Leider hab ich keine Zeit",
                      ]

    def __init__(self, user_id, conditions, repetitions=1):
        super(TextLogger, self).__init__()
        self.user_id = user_id
        self.conditions = conditions
        self.elapsed = 0
        self.word_times = []
        self.trials = []
        self.current_trial = Trial("", "")
        self.current_text = ""
        self.current_input_technique = None
        self.isFirstLetter = True
        self.sentenceTimer = QtCore.QTime()
        self.wordTimer = QtCore.QTime()
        self.init_trials(self.conditions, repetitions)
        self.initUI()
        self.prepareNextTrial()
        print(
            "\"user_id\";\"presented_sentence\";\"transcribed_sentence\";\"text_input_technique\";"
            "\"text_length\";\"total_time\";\"wpm\";\"timestamp (ISO)\"")

    def init_trials(self, conditions, repetitions):
        for i in range(len(conditions)):
            for j in range(repetitions):
                self.trials.append(Trial(conditions[i][0], conditions[i][1]))

    def initUI(self):
        self.setGeometry(0, 0, 400, 200)
        self.setWindowTitle('TextLogger')
        self.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.show()

    def prepareNextTrial(self):
        if self.elapsed < len(self.trials):
            #self.current_trial = self.trials[self.elapsed]
            newTrial = self.trials[self.elapsed]
            if newTrial.get_current_condition()[1] != self.current_trial.get_current_condition()[1]:
                self.startNext = False
                self.current_trial = newTrial
                self.prepareNextTest()
                return;
            self.current_trial = newTrial
            self.isFirstLetter = True
            self.current_text = ""

            self.setText("\n" + self.getNextSentence() + "\n" + "\n" + self.getInputMethodAsString())


            self.elapsed += 1
            self.stop_sentence_time_measurement()
            self.stop_word_time_measurement()
        else:
            sys.stderr.write("All trials done!")
            sys.exit(1)

    def prepareNextTest(self):
        self.removeEventFilter(self.current_input_technique)
        if self.current_trial.get_current_condition()[1] == "C":
            self.setText("Press Space to start the next trial with CHORD input technique")
            self.current_input_technique = input_technique.ChordInputMethod()
            self.installEventFilter(self.current_input_technique)
        else:
            self.setText("Press Space to start the next trial with STANDARD input technique")
            self.current_input_technique = input_technique.StandardInputMethod()
            self.installEventFilter(self.current_input_technique)
        return

    def getNextSentence(self):
        if self.current_trial.get_current_condition()[0] == "S":
            if self.elapsed < len(self.SHORT_SENTENCES):
                return self.SHORT_SENTENCES[self.elapsed]
            return self.SHORT_SENTENCES[randint(0, len(self.SHORT_SENTENCES) - 1)]
        else:
            if self.elapsed < len(self.LONG_SENTENCES):
                return self.LONG_SENTENCES[self.elapsed]
            return self.LONG_SENTENCES[randint(0, len(self.LONG_SENTENCES)- 1)]

    def getInputMethodAsString(self):
        if self.current_trial.get_current_condition()[1] == "C":
            return "Use CHORDINPUT for assistance."
        return "Use the STANDARD TYPING technique."

    ''' Returns a timestamp'''

    def timestamp(self):
        return QtCore.QDateTime.currentDateTime().toString(QtCore.Qt.ISODate)

    def keyPressEvent(self, ev):
        super(TextLogger, self).keyPressEvent(ev)
        # if ev.key() != QtCore.Qt.Key_Return:
        # print(ev.text())
        if ev.key() == QtCore.Qt.Key_Space:
            if not self.startNext:
                self.startNext = True
                self.prepareNextTrial()
                return
            wordTime = self.stop_word_time_measurement()
            self.word_times.append(wordTime)
            # self.logToStdOut(wordTime, False)
            self.start_word_time_measurement()

        self.current_text += ev.text()
        if self.isFirstLetter:
            self.start_sentence_time_measurement()
            self.start_word_time_measurement()
            self.isFirstLetter = False

        if ev.key() == QtCore.Qt.Key_Return:
            wordTime = self.stop_word_time_measurement()
            self.sentenceTime = self.stop_sentence_time_measurement()
            self.word_times.append(wordTime)
            self.logToStdOut(self.SHORT_SENTENCES[self.elapsed - 1], self.current_text, self.calculate_wpm())

            self.prepareNextTrial()

    def calculate_wpm(self):
        if self.sentenceTime == 0:
            return 0
        wpm = (float(len(self.current_text)) / float(self.sentenceTime / 1000)) * (60 / 5)
        return wpm

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

    def logToStdOut(self, presented_text, transcribed_text, wpm):
        transcribed_text = re.sub('\s\s', ' ', transcribed_text)
        transcribed_text = re.sub('\n', '', transcribed_text)
        log_line = "\"%s\";\"%s\";\"%s\";\"%s\";\"%s\";\"%d\";\"%d\";\"%s\"" % (self.user_id, presented_text, self.current_trial.get_current_condition()[1], self.current_trial.get_current_condition()[0],
                                                                                transcribed_text.strip(), self.sentenceTime,
                                                                                wpm, self.timestamp())
        print(log_line)
        """if done:
            print("Time needed for sentence: " + str(time))
            return
        print("Time needed for word: " + str(time))"""


class Trial:
    """
        Stores the settings for a single trial of the experiment

        @param text_input_technique: The text input technique. This can be chord input or standard QWERTZ input
        @param text_length: The length of the text to transcribe (short or long)
    """

    def __init__(self, text_input_technique, text_length):
        self.text_length = text_length
        self.text_input_technique = text_input_technique

    ''' Helper for accessing this trial's settings'''

    def get_current_condition(self):
        return self.text_length, self.text_input_technique


class TextEntryTest:
    def __init__(self):
        pass


def main():
    # try:
    app = QtWidgets.QApplication(sys.argv)
    if len(sys.argv) < 2:
        sys.stderr.write("Usage: %s <setup file>\n" % sys.argv[0])
        sys.exit(1)
    if sys.argv[1].endswith('.ini'):
        user_id, conditions = parse_ini_file(sys.argv[1])
    text_logger = TextLogger(user_id, conditions)
    text_entry_test = TextEntryTest

    sys.exit(app.exec_())
    # except Exception:
    # print("An error occured!")


def parse_ini_file(filename):
    """
        Reads the information from a ini file

        @return: Integer with the user's id; a list with all possible target sizes for this test;
                a list with all possible target distances for this test; Boolean indicating whether the improved
                pointing technique should be used or not
    """
    config = configparser.ConfigParser()
    config.read(filename)
    if 'experiment_setup' in config:
        setup = config['experiment_setup']
        user_id = setup['UserID']
        conditions_string = setup['Conditions']
        # inspired by: https://stackoverflow.com/questions/9763116/parse-a-tuple-from-a-string
        conditions = conditions_string.split(";")
    else:
        print("Error: wrong file format.")
        sys.exit(1)
    return user_id, conditions


if __name__ == '__main__':
    main()
