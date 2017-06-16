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


    def initUI(self):
        self.setGeometry(0, 0, 800, 200)
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
        self.logger.log_event("key_pressed", ev.key(), ev.text())
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
            self.logger.log_stats(self.current_trial, self.current_text, self.sentenceTime, self.calculate_wpm())
            self.prepareNextTrial()

    def calculate_wpm(self):
        if self.sentenceTime == 0:
            return 0
        #wpm = (float(len(self.current_text)) / float(self.sentenceTime / 1000)) * (60 / 5)
        wpm = float(len(self.word_times))*(60 / (self.sentenceTime/1000))
        return wpm

    def keyReleaseEvent(self, ev):
        if not self.startNext:
            return
        self.logger.log_event("key_released", ev.key(), ev.text())
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
        self.stats_logfile = open("stats_user" + str(user_id) + ".csv", "a")
        self.stats_out = csv.DictWriter(self.stats_logfile,
                                  ["user_id", "presented_sentence", "transcribed_sentence", "text_input_technique",
                                   "total_time (ms)", "wpm", "timestamp (ISO)"], delimiter=";", quoting=csv.QUOTE_ALL)
        self.events_logfile = open("events_user" + str(user_id) + ".csv", "a")
        self.events_out = csv.DictWriter(self.events_logfile,
                                        ["user_id", "event_type", "event_key", "event_text", "timestamp (ISO)"], delimiter=";",
                                        quoting=csv.QUOTE_ALL)
        if self.print_file:
            self.stats_out.writeheader()
            self.events_out.writeheader()
        print("Fields for stats logging: "
            "\"user_id\";\"presented_sentence\";\"transcribed_sentence\";\"text_input_technique\";"
            "\"total_time\";\"wpm\";\"timestamp (ISO)\"")
        print("Fields for event logging: "
              "\"user_id\";\"event_type\";\"event_key\";\"event_text\";\"timestamp (ISO)\"")

    def log_stats(self, trial, transcribed_text, time_needed, wpm):
        transcribed_text = re.sub('\s\s', ' ', transcribed_text)
        transcribed_text = re.sub('\n', '', transcribed_text)
        log_line = "\"%s\";\"%s\";\"%s\";\"%s\";\"%d\";\"%f\";\"%s\"" % (self.user_id, trial.get_text(), trial.get_text_input_technique(),
                                                                                transcribed_text.strip(), time_needed,
                                                                                wpm, self.timestamp())
        if self.print_log:
            print(log_line)

        current_values = {"user_id": self.user_id, "presented_sentence": trial.get_text(),
                          "transcribed_sentence": transcribed_text.strip(), "text_input_technique": trial.get_text_input_technique(),
                          "total_time (ms)": time_needed,
                          "wpm": wpm, "timestamp (ISO)": self.timestamp()}
        if self.print_file:
            self.stats_out.writerow(current_values)
        return

    def log_event(self, type, key, text):
        if key == QtCore.Qt.Key_Return:
            text = "return"

        log_line = "\"%s\";\"%s\";\"%s\";\"%s\";\"%s\"" % (self.user_id, type, key, text, self.timestamp())
        if self.print_log:
            print(log_line)

        current_values = {"user_id": self.user_id, "event_type": type, "event_key": key,
                          "event_text": text, "timestamp (ISO)": self.timestamp()}
        if self.print_file:
            self.events_out.writerow(current_values)
        return


    ''' Returns a timestamp'''
    @staticmethod
    def timestamp():
        return QtCore.QDateTime.currentDateTime().toString(QtCore.Qt.ISODate)


class Trial:
    """
        Stores the settings for a single trial of the experiment

        @param text_input_technique: The text input technique. This can be chord input or standard QWERTZ input
    """

    SENTENCES = ["Der Mann ging nie spazieren.", "Mein Hund hat dich lieb.", "Viele Leute mögen dich.",
                      "Der Junge weiß nicht was er tut.", "Ich hab den Termin verpasst.", "Leider hab ich keine Zeit."]

    INPUT_CHORD = "C"
    INPUT_STANDARD = "S"

    def __init__(self, text_input_technique, text):
        self.text_input_technique = text_input_technique
        self.text = text

    @staticmethod
    def create_list_from_conditions(conditions, repetitions=4):
        trials = []
        for i in range(len(conditions)):
            for j in range(repetitions):
                trials.append(Trial(conditions[i], Trial.get_sentence_from_list(len(trials))))
        return trials

    @staticmethod
    def get_sentence_from_list(idx):
        if idx < len(Trial.SENTENCES):
            return Trial.SENTENCES[idx]
        return Trial.SENTENCES[randint(0, len(Trial.SENTENCES) - 1)]

    def get_text(self):
        return self.text

    def get_text_input_technique(self):
        return self.text_input_technique


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
