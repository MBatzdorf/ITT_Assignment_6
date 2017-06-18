#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import configparser
from PyQt5 import Qt, QtGui, QtCore, QtWidgets
import re
import csv
import random
import text_input_technique as input_technique


class TextTest(QtWidgets.QTextEdit):
    def __init__(self, userId, conditions, isTraining, repetitions=2):
        super(TextTest, self).__init__()
        self.initVariables(userId, conditions, isTraining, repetitions)
        self.initUI()
        self.prepareNextTrial()

    def initVariables(self, userId, conditions, isTraining, repetitions):
        self.elapsed = 0
        self.wordTimes = []
        self.trials = Trial.create_list_from_conditions(conditions, repetitions)
        self.currentTrial = self.trials[0]
        self.currentText = ""
        self.currentWord = ""
        self.currentInputTechnique = None
        self.setInputTechnique(self.currentTrial.get_text_input_technique())
        self.startNext = False
        self.isFirstLetter = True
        self.sentenceTimer = QtCore.QTime()
        self.wordTimer = QtCore.QTime()
        self.logger = TestLogger(userId, True, True, isTraining)

    def initUI(self):
        self.setGeometry(0, 0, 800, 200)
        self.setWindowTitle('TextLogger')
        self.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.show()

    def prepareNextTrial(self):
        if self.elapsed < len(self.trials):
            newTrial = self.trials[self.elapsed]
            if newTrial.get_text_input_technique() != self.currentTrial.get_text_input_technique() or \
                    not self.startNext:
                self.startNext = False
                self.currentTrial = newTrial
                self.showInstructions()
                self.setInputTechnique(self.currentTrial.get_text_input_technique())
                return
            self.currentTrial = newTrial
            self.isFirstLetter = True
            self.currentText = ""
            self.setText("\n" + self.currentTrial.get_text())
            self.elapsed += 1
        else:
            self.endTest()

    def endTest(self):
        sys.stderr.write("All trials done!")
        self.deleteLater()

    def showInstructions(self):
        if self.currentTrial.get_text_input_technique() == Trial.INPUT_CHORD:
            self.setText("Press Space to start the next trial with CHORD input technique")
        else:
            self.setText("Press Space to start the next trial with STANDARD input technique")
        return

    def setInputTechnique(self, identifier):
        self.removeEventFilter(self.currentInputTechnique)
        if identifier == Trial.INPUT_CHORD:
            self.currentInputTechnique = input_technique.ChordInputMethod()
            self.installEventFilter(self.currentInputTechnique)
        else:
            self.currentInputTechnique = input_technique.StandardInputMethod()
            self.installEventFilter(self.currentInputTechnique)
        return

    def keyPressEvent(self, ev):
        if not self.startNext:
            if ev.key() == QtCore.Qt.Key_Space:
                self.startNext = True
                self.prepareNextTrial()
            return
        self.logger.log_event("key_pressed", ev.key(), ev.text())
        super(TextTest, self).keyPressEvent(ev)
        self.currentText += ev.text()
        self.currentWord += ev.text()
        if self.isFirstLetter:
            self.startSentenceTimeMeasurement()
            self.startWordTimeMeasurement()
            self.isFirstLetter = False

        if ev.key() == QtCore.Qt.Key_Space:
            wordTime = self.stopWordTimeMeasurement()
            self.logger.log_event("word_typed", ev.key(), self.currentWord)
            self.currentWord = ""
            self.wordTimes.append(wordTime)
            self.startWordTimeMeasurement()

        if ev.key() == QtCore.Qt.Key_Return:
            wordTime = self.stopWordTimeMeasurement()
            self.sentenceTime = self.stopSentenceTimeMeasurement()
            self.logger.log_event("word_typed", ev.key(), self.currentWord)
            self.logger.log_event("sentence_typed", ev.key(), self.currentText)
            self.currentWord = ""
            self.wordTimes.append(wordTime)
            self.logger.log_stats(self.currentTrial, self.currentText, self.sentenceTime, self.calculateWpm())
            self.prepareNextTrial()

    def calculateWpm(self):
        if self.sentenceTime == 0:
            return 0
        # followed formula from http://www.yorku.ca/mack/RN-TextEntrySpeed.html
        wpm = (float(len(self.currentText)) / float(self.sentenceTime / 1000)) * (60 / 5)
        # wpm = float(len(self.wordTimes)) * (60 / (self.sentenceTime / 1000))
        return wpm

    def keyReleaseEvent(self, ev):
        if not self.startNext:
            return
        self.logger.log_event("key_released", ev.key(), ev.text())
        super(TextTest, self).keyReleaseEvent(ev)

    def startSentenceTimeMeasurement(self):
        self.sentenceTimer.start()

    def stopSentenceTimeMeasurement(self):
        time_needed = self.sentenceTimer.elapsed()
        return time_needed

    def startWordTimeMeasurement(self):
        self.wordTimer.start()

    def stopWordTimeMeasurement(self):
        time_needed = self.wordTimer.elapsed()
        return time_needed


class TextTraining(TextTest):
    def __init__(self, userId, trainingInputTechnique, testToStartAfter=None, repetitions=1):
        super(TextTraining, self).__init__(userId, trainingInputTechnique, True, repetitions)
        self.logger.disable_stdout_logging()
        self.logger.disable_file_logging()
        self.testToStart = testToStartAfter
        if self.testToStart is not None:
            self.testToStart.hide()

    def initVariables(self, userId, trainingInputTechnique, isTraining, repetitions):
        super().initVariables(userId, trainingInputTechnique, isTraining, repetitions)
        self.trials = Trial.get_training_set(trainingInputTechnique, repetitions)
        self.currentTrial = self.trials[0]
        self.setInputTechnique(self.currentTrial.get_text_input_technique())

    def showInstructions(self):
        if self.currentTrial.get_text_input_technique() == Trial.INPUT_CHORD:
            self.setText("Press Space to start the TRAINING Trial using CHORD INPUT!")
        else:
            self.setText("Press Space to start the TRAINING Trial using STANDARD INPUT!")
        return

    def endTest(self):
        sys.stderr.write("All trials done!")
        if self.testToStart is not None:
            self.testToStart.show()
        self.deleteLater()


class TestLogger(object):
    def __init__(self, user_id, log_to_stdout, log_to_file, isTraining):
        super(TestLogger, self).__init__()
        self.log_to_stdout = log_to_stdout
        self.log_to_file = log_to_file
        self.isTraining = isTraining
        self.user_id = user_id
        self.init_logging()

    def init_logging(self):
        self.stats_logfile = open("stats_user" + str(self.user_id) + ".csv", "a")
        self.stats_out = csv.DictWriter(self.stats_logfile,
                                        ["user_id", "presented_sentence", "transcribed_sentence",
                                         "text_input_technique",
                                         "total_time (ms)", "wpm", "timestamp (ISO)"], delimiter=";",
                                        quoting=csv.QUOTE_ALL)
        self.events_logfile = open("events_user" + str(self.user_id) + ".csv", "a")
        self.events_out = csv.DictWriter(self.events_logfile,
                                         ["user_id", "event_type", "event_key", "event_text", "timestamp (ISO)"],
                                         delimiter=";",
                                         quoting=csv.QUOTE_ALL)
        if not self.isTraining:
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
        if self.log_to_stdout:
            print(log_line)

        current_values = {"user_id": self.user_id, "presented_sentence": trial.get_text(),
                          "transcribed_sentence": transcribed_text.strip(),
                          "text_input_technique": trial.get_text_input_technique(),
                          "total_time (ms)": time_needed,
                          "wpm": wpm, "timestamp (ISO)": self.timestamp()}
        if self.log_to_file:
            self.stats_out.writerow(current_values)
        return

    def log_event(self, type, key, text):
        if key == QtCore.Qt.Key_Return:
            key = "return"
            text = "\\n"

        if key == QtCore.Qt.Key_Space:
            key = "space"
            text = " "

        log_line = "\"%s\";\"%s\";\"%s\";\"%s\";\"%s\"" % (self.user_id, type, key, text.strip(), self.timestamp())
        if self.log_to_stdout:
            print(log_line)

        current_values = {"user_id": self.user_id, "event_type": type, "event_key": key,
                          "event_text": text, "timestamp (ISO)": self.timestamp()}
        if self.log_to_file:
            self.events_out.writerow(current_values)
        return

    ''' Returns a timestamp'''

    @staticmethod
    def timestamp():
        return QtCore.QDateTime.currentDateTime().toString(QtCore.Qt.ISODate)

    def disable_stdout_logging(self):
        self.log_to_stdout = False
        return

    def disable_file_logging(self):
        self.log_to_file = False
        return


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
                 "wo rennst du bloß rein", "es war ein Mann ich sehe ihn nicht.", "ich mag ein Eis es ist heiß hier",
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

    def get_text(self):
        return self.text

    def get_text_input_technique(self):
        return self.text_input_technique

    @staticmethod
    def get_training_set(input_technique, repetitions):
        training_trials = []
        Trial.TRAINING_SENTENCES = repetitions * Trial.TRAINING_SENTENCES
        for i in range(len(Trial.TRAINING_SENTENCES)):
            training_trials.append(Trial(input_technique, Trial.TRAINING_SENTENCES[i]))
        return training_trials


def main():
    app = QtWidgets.QApplication(sys.argv)
    if len(sys.argv) < 2:
        sys.stderr.write("Usage: %s <setup file>\n" % sys.argv[0])
        sys.exit(1)
    if sys.argv[1].endswith('.ini'):
        user_id, conditions = parse_ini_file(sys.argv[1])
    text_training = TextTraining(user_id, "C", TextTest(user_id, conditions, False))
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
