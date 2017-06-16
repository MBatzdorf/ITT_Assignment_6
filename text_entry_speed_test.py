#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import configparser
from PyQt5 import Qt, QtGui, QtCore, QtWidgets
import re
import csv
import random
from random import randint
import text_input_technique as input_technique


class TextTest(QtWidgets.QTextEdit):
    def __init__(self, user_id, conditions, repetitions=1):
        super(TextTest, self).__init__()
        self.elapsed = 0
        self.training_elapsed = 0
        self.word_times = []
        self.trials = Trial.create_list_from_conditions(conditions, repetitions)
        self.training_set = Trial.get_training_set(repetitions=1)
        self.current_trial = self.trials[0]
        self.current_text = ""
        self.current_word = ""
        self.current_input_technique = None
        self.setInputTechnique(self.current_trial.get_text_input_technique())
        self.startNext = False
        self.isTraining = False
        self.isFirstLetter = True
        self.sentenceTimer = QtCore.QTime()
        self.wordTimer = QtCore.QTime()
        self.logger = TestLogger(user_id, True, True)
        self.initUI()
        self.startTraining()
        self.prepareNextTrial()

    def startTraining(self):
        self.isTraining = True

    def showTrainingInstructions(self):
        self.setText("Press Space to start the TRAINING Trial using CHORD INPUT!")

    def initUI(self):
        self.setGeometry(0, 0, 800, 200)
        self.setWindowTitle('TextLogger')
        self.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.showTrainingInstructions()
        self.show()

    def prepareNextTrial(self):
        if not self.isTraining:
            if self.elapsed < len(self.trials):
                newTrial = self.trials[self.elapsed]
                if newTrial.get_text_input_technique() != self.current_trial.get_text_input_technique() or \
                        not self.startNext:
                    self.startNext = False
                    self.current_trial = newTrial
                    self.showInstructions()
                    self.setInputTechnique(self.current_trial.get_text_input_technique())
                    return
                self.current_trial = newTrial
                self.isFirstLetter = True
                self.current_text = ""
                self.setText("\n" + self.current_trial.get_text())
                self.elapsed += 1
            else:
                sys.stderr.write("All trials done!")
                sys.exit(1)
        elif self.isTraining:
            if self.training_elapsed < len(self.training_set):
                newTrial = self.training_set[self.training_elapsed]
                if newTrial.get_text_input_technique() != self.current_trial.get_text_input_technique() or \
                        not self.startNext:
                    self.startNext = False
                    self.current_trial = newTrial
                    # self.showInstructions()
                    self.setInputTechnique(self.current_trial.get_text_input_technique())
                    return
                self.current_trial = newTrial
                self.isFirstLetter = True
                self.current_text = ""
                self.setText("\n" + self.current_trial.get_text())
                self.training_elapsed += 1
            else:
                self.isTraining = False
                self.startNext = False
                self.showInstructions()


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
        if not self.isTraining:
            self.logger.log_event("key_pressed", ev.key(), ev.text())
        super(TextTest, self).keyPressEvent(ev)
        self.current_text += ev.text()
        self.current_word += ev.text()
        if self.isFirstLetter:
            self.start_sentence_time_measurement()
            self.start_word_time_measurement()
            self.isFirstLetter = False

        if ev.key() == QtCore.Qt.Key_Space:
            if not self.isTraining:
                wordTime = self.stop_word_time_measurement()
                self.logger.log_event("word_typed", ev.key(), self.current_word)
                self.current_word = ""
                self.word_times.append(wordTime)
                self.start_word_time_measurement()

        if ev.key() == QtCore.Qt.Key_Return:
            if not self.isTraining:
                wordTime = self.stop_word_time_measurement()
                self.sentenceTime = self.stop_sentence_time_measurement()
                self.logger.log_event("word_typed", ev.key(), self.current_word)
                self.logger.log_event("sentence_typed", ev.key(), self.current_text)
                self.current_word = ""
                self.word_times.append(wordTime)
                self.logger.log_stats(self.current_trial, self.current_text, self.sentenceTime, self.calculate_wpm())
            self.prepareNextTrial()

    def calculate_wpm(self):
        if self.sentenceTime == 0:
            return 0
        # wpm = (float(len(self.current_text)) / float(self.sentenceTime / 1000)) * (60 / 5)
        wpm = float(len(self.word_times)) * (60 / (self.sentenceTime / 1000))
        return wpm

    def keyReleaseEvent(self, ev):
        if not self.startNext:
            return
        if not self.isTraining:
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
                                        ["user_id", "presented_sentence", "transcribed_sentence",
                                         "text_input_technique",
                                         "total_time (ms)", "wpm", "timestamp (ISO)"], delimiter=";",
                                        quoting=csv.QUOTE_ALL)
        self.events_logfile = open("events_user" + str(user_id) + ".csv", "a")
        self.events_out = csv.DictWriter(self.events_logfile,
                                         ["user_id", "event_type", "event_key", "event_text", "timestamp (ISO)"],
                                         delimiter=";",
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
        log_line = "\"%s\";\"%s\";\"%s\";\"%s\";\"%d\";\"%f\";\"%s\"" % (
            self.user_id, trial.get_text(), trial.get_text_input_technique(),
            transcribed_text.strip(), time_needed,
            wpm, self.timestamp())
        if self.print_log:
            print(log_line)

        current_values = {"user_id": self.user_id, "presented_sentence": trial.get_text(),
                          "transcribed_sentence": transcribed_text.strip(),
                          "text_input_technique": trial.get_text_input_technique(),
                          "total_time (ms)": time_needed,
                          "wpm": wpm, "timestamp (ISO)": self.timestamp()}
        if self.print_file:
            self.stats_out.writerow(current_values)
        return

    def log_event(self, type, key, text):
        if key == QtCore.Qt.Key_Return:
            key = "return"

        if key == QtCore.Qt.Key_Space:
            key = "space"

        log_line = "\"%s\";\"%s\";\"%s\";\"%s\";\"%s\"" % (self.user_id, type, key, text.strip(), self.timestamp())
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
    TRAINING_SENTENCES = ["der Mann ging im Herbst mal allein spazieren", "der Junge weiß echt nicht was er tut",
                          "ich hab den Termin verpasst", "das Spiel ist gut schieß nen Punkt",
                          "wir essen zu viel Fleisch iss Gemüse"]

    SENTENCES = ["der Mann ging im Herbst mal allein spazieren", "mein Hund hat dich extrem lieb",
                 "Die Leute mögen dich ich mag dich auch",
                 "der Junge weiß echt nicht was er tut", "ich hab den Termin verpasst", "leider hab ich keine Zeit",
                 "wo rennst du nur rein", "es war ein Mann ich sehe ihn nicht.", "ich mag ein Eis es ist heiß hier",
                 "geh nun zum Auto es ist kalt hier", "der hat nen Hut aber ich nicht",
                 "das Spiel ist gut schieß nen Punkt", "wir essen zu viel Fleisch iss Gemüse"]

    INPUT_CHORD = "C"
    INPUT_STANDARD = "S"

    def __init__(self, text_input_technique, text):
        self.text_input_technique = text_input_technique
        self.text = text

    @staticmethod
    def create_list_from_conditions(conditions, repetitions):
        trials = []
        Trial.SENTENCES = repetitions * Trial.SENTENCES
        # print(trials)

        for i in range(len(conditions)):
            random.shuffle(Trial.SENTENCES)
            for j in range(len(Trial.SENTENCES)):
                trials.append(Trial(conditions[i], Trial.get_sentence_from_list(len(trials))))
        return trials

    @staticmethod
    def get_sentence_from_list(idx):
        if idx < len(Trial.SENTENCES):
            return Trial.SENTENCES[idx]
        else:
            return Trial.SENTENCES[len(Trial.SENTENCES) - 1 - idx]
            # return Trial.SENTENCES[randint(0, len(Trial.SENTENCES) - 1)]

    def get_text(self):
        return self.text

    def get_text_input_technique(self):
        return self.text_input_technique

    @staticmethod
    def get_training_set(repetitions):
        training_trials = []
        Trial.TRAINING_SENTENCES = repetitions * Trial.TRAINING_SENTENCES
        for i in range(len(Trial.TRAINING_SENTENCES)):
            training_trials.append(Trial("C", Trial.TRAINING_SENTENCES[i]))
        return training_trials


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

    # except Exception:
    #    print("An error occured!")


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
