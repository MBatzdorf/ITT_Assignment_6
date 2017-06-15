#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import configparser
from PyQt5 import Qt, QtGui, QtCore, QtWidgets
import re
import csv
from random import randint
import text_input_technique as input_technique


class TextLogger(QtWidgets.QTextEdit):
    SHORT_SENTENCES = ["Wo rennst du hin.", "Ich sehe dich nicht.", "Es war ein Mann.", "Ich mag das Eis.",
                       "Geh nun zum Auto.", "Der hat einen Hut.", "Es ist heiß hier.", "Das Spiel ist gut!",
                       "Wir essen zu viel!", "Schieß ein Tor!"]
    LONG_SENTENCES = ["Der Mann ging nie spazieren.", "Mein Hund hat dich lieb.", "Viele Leute mögen dich.",
                      "Der Junge weiß nicht was er tut.", "Ich hab den Termin verpasst.", "Leider hab ich keine Zeit.",
                      ]

    def __init__(self, user_id, conditions, repetitions=4):
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
        self.initLogging()
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

    def initLogging(self):
        self.logfile = open("user" + str(self.user_id) + ".csv", "a")
        self.out = csv.DictWriter(self.logfile,
                                  ["user_id", "presented_sentence", "transcribed_sentence", "text_input_technique", "text_length",
                                   "total_time (ms)", "wpm", "timestamp (ISO)"], delimiter=";", quoting=csv.QUOTE_ALL)
        self.out.writeheader()

    def prepareNextTrial(self):
        if self.elapsed < len(self.trials):
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
    @staticmethod
    def timestamp():
        return QtCore.QDateTime.currentDateTime().toString(QtCore.Qt.ISODate)

    def keyPressEvent(self, ev):
        super(TextLogger, self).keyPressEvent(ev)

        if not self.startNext:
            if ev.key() == QtCore.Qt.Key_Space:
                self.startNext = True
                self.prepareNextTrial()
            return

        self.current_text += ev.text()
        if self.isFirstLetter:
            self.start_sentence_time_measurement()
            self.start_word_time_measurement()
            self.isFirstLetter = False

        if ev.key() == QtCore.Qt.Key_Space:
            wordTime = self.stop_word_time_measurement()
            self.word_times.append(wordTime)
            self.start_word_time_measurement()

        if ev.key() == QtCore.Qt.Key_Return:
            wordTime = self.stop_word_time_measurement()
            self.sentenceTime = self.stop_sentence_time_measurement()
            self.word_times.append(wordTime)
            self.logTime(self.SHORT_SENTENCES[self.elapsed - 1], self.current_text, self.calculate_wpm())

            self.prepareNextTrial()

    def calculate_wpm(self):
        if self.sentenceTime == 0:
            return 0
        #wpm = (float(len(self.current_text)) / float(self.sentenceTime / 1000)) * (60 / 5)
        wpm = float(len(self.word_times))*(60 / (self.sentenceTime/1000))
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

    def logTime(self, presented_text, transcribed_text, wpm):
        transcribed_text = re.sub('\s\s', ' ', transcribed_text)
        transcribed_text = re.sub('\n', '', transcribed_text)
        log_line = "\"%s\";\"%s\";\"%s\";\"%s\";\"%s\";\"%d\";\"%f\";\"%s\"" % (self.user_id, presented_text, self.current_trial.get_current_condition()[1], self.current_trial.get_current_condition()[0],
                                                                                transcribed_text.strip(), self.sentenceTime,
                                                                                wpm, self.timestamp())
        print(log_line)
        current_values = {"user_id": self.user_id, "presented_sentence": presented_text,
                          "transcribed_sentence": self.current_trial.get_current_condition()[1], "text_input_technique": self.current_trial.get_current_condition()[0],
                          "text_length": transcribed_text.strip(), "total_time (ms)": self.sentenceTime,
                          "wpm": wpm, "timestamp (ISO)": self.timestamp()}
        self.out.writerow(current_values)


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
