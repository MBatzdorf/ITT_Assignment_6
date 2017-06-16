#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import configparser
from PyQt5 import Qt, QtGui, QtCore, QtWidgets
import re
import csv
from random import randint
import text_input_technique as input_technique


class TextTest(QtWidgets.QTextEdit):

    def __init__(self, user_id, conditions, repetitions=1):
        super(TextTest, self).__init__()
        self.elapsed = 0
        self.word_times = []
        self.trials = Trial.create_list_from_conditions(conditions, repetitions)
        self.current_trial = self.trials[0]
        self.current_text = ""
        self.current_input_technique = None
        self.setInputTechnique(self.current_trial.get_text_input_technique())
        self.startNext = False
        self.isFirstLetter = True
        self.sentenceTimer = QtCore.QTime()
        self.wordTimer = QtCore.QTime()
        self.logger = TestLogger(user_id, True, True)
        self.initUI()
        self.prepareNextTrial()
        print(
            "\"user_id\";\"presented_sentence\";\"transcribed_sentence\";\"text_input_technique\";"
            "\"text_length\";\"total_time\";\"wpm\";\"timestamp (ISO)\"")

    def initUI(self):
        self.setGeometry(0, 0, 400, 200)
        self.setWindowTitle('TextLogger')
        self.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.showInstructions()
        self.show()

    def prepareNextTrial(self):
        if self.elapsed < len(self.trials):
            newTrial = self.trials[self.elapsed]
            if newTrial.get_text_input_technique() != self.current_trial.get_text_input_technique() or not self.startNext:
                self.startNext = False
                self.current_trial = newTrial
                self.showInstructions()
                self.setInputTechnique(self.current_trial.get_text_input_technique())
                return;
            self.current_trial = newTrial
            self.isFirstLetter = True
            self.current_text = ""
            self.setText("\n" + self.current_trial.get_text())
            self.elapsed += 1
        else:
            sys.stderr.write("All trials done!")
            sys.exit(1)

    def showInstructions(self):
        if self.current_trial.get_text_input_technique() == Trial.INPUT_CHORD:
            self.setText("Press Space to start the next trial with CHORD input technique")
        else:
            self.setText("Press Space to start the next trial with STANDARD input technique")
        return

    def setInputTechnique(self, identifier):
        self.removeEventFilter(self.current_input_technique)
        if identifier == Trial.INPUT_CHORD:
            self.current_input_technique = input_technique.ChordInputMethod()
            self.installEventFilter(self.current_input_technique)
        else:
            self.current_input_technique = input_technique.StandardInputMethod()
            self.installEventFilter(self.current_input_technique)
        return

    def keyPressEvent(self, ev):
        if not self.startNext:
            if ev.key() == QtCore.Qt.Key_Space:
                self.startNext = True
                self.prepareNextTrial()
            return

        super(TextTest, self).keyPressEvent(ev)

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
            self.logger.log_time(self.current_trial, self.current_text, self.sentenceTime, self.calculate_wpm())
            self.prepareNextTrial()

    def calculate_wpm(self):
        if self.sentenceTime == 0:
            return 0
        #wpm = (float(len(self.current_text)) / float(self.sentenceTime / 1000)) * (60 / 5)
        wpm = float(len(self.word_times))*(60 / (self.sentenceTime/1000))
        return wpm

    def keyReleaseEvent(self, ev):
        super(TextTest, self).keyReleaseEvent(ev)

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


class TestLogger(object):
    def __init__(self, user_id, print_to_log, print_to_file):
        super(TestLogger, self).__init__()
        self.print_log = print_to_log
        self.print_file = print_to_file
        self.user_id = user_id
        self.logfile = open("user" + str(user_id) + ".csv", "a")
        self.out = csv.DictWriter(self.logfile,
                                  ["user_id", "presented_sentence", "transcribed_sentence", "text_input_technique",
                                   "text_length",
                                   "total_time (ms)", "wpm", "timestamp (ISO)"], delimiter=";", quoting=csv.QUOTE_ALL)
        if self.print_file:
            self.out.writeheader()

    def log_time(self, trial, transcribed_text, time_needed, wpm):
        transcribed_text = re.sub('\s\s', ' ', transcribed_text)
        transcribed_text = re.sub('\n', '', transcribed_text)
        log_line = "\"%s\";\"%s\";\"%s\";\"%s\";\"%s\";\"%d\";\"%f\";\"%s\"" % (self.user_id, trial.get_text(), trial.get_text_input_technique(), trial.get_text_length(),
                                                                                transcribed_text.strip(), time_needed,
                                                                                wpm, self.timestamp())
        if self.print_log:
            print(log_line)

        current_values = {"user_id": self.user_id, "presented_sentence": trial.get_text(),
                          "transcribed_sentence": transcribed_text.strip(), "text_input_technique": trial.get_text_input_technique(),
                          "text_length": trial.get_text_length(), "total_time (ms)": time_needed,
                          "wpm": wpm, "timestamp (ISO)": self.timestamp()}
        if self.print_file:
            self.out.writerow(current_values)
        return


    ''' Returns a timestamp'''
    @staticmethod
    def timestamp():
        return QtCore.QDateTime.currentDateTime().toString(QtCore.Qt.ISODate)


class Trial:
    """
        Stores the settings for a single trial of the experiment

        @param text_input_technique: The text input technique. This can be chord input or standard QWERTZ input
        @param text_length: The length of the text to transcribe (short or long)
    """

    SHORT_SENTENCES = ["Wo rennst du hin.", "Ich sehe dich nicht.", "Es war ein Mann.", "Ich mag das Eis.",
                       "Geh nun zum Auto.", "Der hat einen Hut.", "Es ist heiß hier.", "Das Spiel ist gut!",
                       "Wir essen zu viel!", "Schieß ein Tor!"]
    LONG_SENTENCES = ["Der Mann ging nie spazieren.", "Mein Hund hat dich lieb.", "Viele Leute mögen dich.",
                      "Der Junge weiß nicht was er tut.", "Ich hab den Termin verpasst.", "Leider hab ich keine Zeit.",
                      ]

    INPUT_CHORD = "C"
    INPUT_STANDARD = "S"

    def __init__(self, text_input_technique, text_length, text):
        self.text_length = text_length
        self.text_input_technique = text_input_technique
        self.text = text

    @staticmethod
    def create_list_from_conditions(conditions, repetitions=4):
        trials = []
        for i in range(len(conditions)):
            for j in range(repetitions):
                trials.append(Trial(conditions[i][0], conditions[i][1], Trial.get_sentence_from_list(conditions[i][0], len(trials))))
        return trials

    @staticmethod
    def get_sentence_from_list(type, idx):
        if type == Trial.INPUT_STANDARD:
            if idx < len(Trial.SHORT_SENTENCES):
                return Trial.SHORT_SENTENCES[idx]
            return Trial.SHORT_SENTENCES[randint(0, len(Trial.SHORT_SENTENCES) - 1)]
        else:
            if idx < len(Trial.LONG_SENTENCES):
                return Trial.LONG_SENTENCES[idx]
            return Trial.LONG_SENTENCES[randint(0, len(Trial.LONG_SENTENCES)- 1)]

    ''' Helper for accessing this trial's settings'''
    def get_current_condition(self):
        return self.text_length, self.text_input_technique

    def get_text(self):
        return self.text

    def get_text_input_technique(self):
        return self.text_input_technique

    def get_text_length(self):
        return self.text_length


def main():
    # try:
    app = QtWidgets.QApplication(sys.argv)
    if len(sys.argv) < 2:
        sys.stderr.write("Usage: %s <setup file>\n" % sys.argv[0])
        sys.exit(1)
    if sys.argv[1].endswith('.ini'):
        user_id, conditions = parse_ini_file(sys.argv[1])
    text_logger = TextTest(user_id, conditions)

    sys.exit(app.exec_())


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
