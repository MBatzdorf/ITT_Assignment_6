#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import configparser

try:
    from PyQt5 import Qt, QtGui, QtCore, QtWidgets
except ImportError:
    print("Could not import PyQt!")
import re
import csv
import random

try:
    import text_input_technique as input_technique
except ImportError:
    print("Could not import text_input_technique.py!")

# This script was created by Alexander Frummet and Marco Batzdorf
# and is based on the "textedit.py" script

""" setup ini file format (S = Standard Input; C = Chord Input):
[experiment_setup]
UserID = 1
Conditions = S;C
"""


class TextTest(QtWidgets.QTextEdit):
    """
        Controller class for performing a test on text input speed

        @param userId: The user's id; used for logging
        @param conditions: A list with conditions for the tests that are to run
        @param isTraining:
        @param repetitions: Defines how often the test is repeated for a single condition
    """

    def __init__(self, userId, conditions, repetitions=2):
        super(TextTest, self).__init__()
        self.elapsed = 0
        self.wordTimes = []
        self.currentText = ""
        self.currentWord = ""
        self.currentInputTechnique = None
        self.startNext = False
        self.isFirstLetter = True
        self.sentenceTimer = QtCore.QTime()
        self.wordTimer = QtCore.QTime()
        self.initVariables(userId, conditions, repetitions)
        self.initUI()
        self.prepareNextTrial()

    ''' Sets up all variables needed to perform a test

        @param userId: The user's id; used for logging
        @param conditions: A list with conditions for the tests that are to run
        @param isTraining:
        @param repetitions: Defines how often the test is repeated for a single condition
    '''

    def initVariables(self, userId, conditions, repetitions):
        self.trials = Trial.create_list_from_conditions(conditions, repetitions)
        self.currentTrial = self.trials[0]
        self.setInputTechnique(self.currentTrial.get_text_input_technique())
        self.logger = TestLogger(userId, True, True)

    ''' Set up the UI settings and show it to the user'''

    def initUI(self):
        self.setGeometry(0, 0, 800, 200)
        self.setWindowTitle('TextLogger')
        self.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.show()

    ''' Chooses the next trial to complete, resets variables necessary to do so
        Exits the application if all trials are completed '''

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

    ''' Tells qt to delete this widget from the viewport '''

    def endTest(self):
        self.logger.log_event("test_finished", "return", "Test finished! All trials done!")
        sys.stderr.write("All trials done!")
        self.deleteLater()

    ''' Shows the instructions for corresponding condition '''

    def showInstructions(self):
        if self.currentTrial.get_text_input_technique() == Trial.INPUT_CHORD:
            self.setText("Press Space to start the next trial with CHORD input technique")
        else:
            self.setText("Press Space to start the next trial with STANDARD input technique")
        return

    ''' Sets a new input technique (as input filter) and removes the old one

        @param identifier: Input technique to install
    '''

    def setInputTechnique(self, identifier):
        self.removeEventFilter(self.currentInputTechnique)
        if identifier == Trial.INPUT_CHORD:
            self.currentInputTechnique = input_technique.ChordInputMethod()
            self.installEventFilter(self.currentInputTechnique)
        else:
            self.currentInputTechnique = input_technique.StandardInputMethod()
            self.installEventFilter(self.currentInputTechnique)
        return

    ''' Handles key press events received from the input filter '''

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

    ''' Calculates the amount of words per minute on the basis of the written sentence'''

    def calculateWpm(self):
        if self.sentenceTime == 0:
            return 0
        # followed formula from http://www.yorku.ca/mack/RN-TextEntrySpeed.html
        wpm = (float(len(self.currentText)) / float(self.sentenceTime / 1000)) * (60 / 5)
        return wpm

    ''' Handles key release events received from the input filter '''

    def keyReleaseEvent(self, ev):
        if not self.startNext:
            return
        self.logger.log_event("key_released", ev.key(), ev.text())
        super(TextTest, self).keyReleaseEvent(ev)

    ''' Starts the time measurement for writing a whole sentence '''

    def startSentenceTimeMeasurement(self):
        self.sentenceTimer.start()

    ''' Stops the time measurement for writing a whole sentence
        @return: The time needed to write the whole sentence presented to the user
    '''

    def stopSentenceTimeMeasurement(self):
        time_needed = self.sentenceTimer.elapsed()
        return time_needed

    ''' Starts the time measurement for writing a single word  '''

    def startWordTimeMeasurement(self):
        self.wordTimer.start()

    ''' Stops the time measurement for writing a single word
        @return: The time needed to write the last word typed
    '''

    def stopWordTimeMeasurement(self):
        time_needed = self.wordTimer.elapsed()
        return time_needed


class TextTraining(TextTest):
    """
        Controller class for performing a test on text input speed

        @param userId: The user's id
        @param trainingInputTechnique: Defines which input technique should be used for training
        @param testToStartAfter: Tells the training which actual test to start afterwards
        @param repetitions: Defines how often the training is repeated for a single condition
    """

    def __init__(self, userId, trainingInputTechnique, testToStartAfter=None, repetitions=3):
        super(TextTraining, self).__init__(userId, trainingInputTechnique, repetitions)
        self.testToStart = testToStartAfter
        if self.testToStart is not None:
            self.testToStart.hide()

    ''' Sets up all variables needed to perform a test

        @param userId: The user's id
        @param trainingInputTechnique: Defines which input technique should be used for training
        @param testToStartAfter: Tells the training which actual test to start afterwards
        @param repetitions: Defines how often the training is repeated for a single condition
    '''

    def initVariables(self, userId, trainingInputTechnique, repetitions):
        self.trials = Trial.get_training_set(trainingInputTechnique, repetitions)
        self.currentTrial = self.trials[0]
        self.setInputTechnique(self.currentTrial.get_text_input_technique())
        self.logger = TestLogger(userId, False, False)

    ''' Shows the instructions for the current training session '''

    def showInstructions(self):
        if self.currentTrial.get_text_input_technique() == Trial.INPUT_CHORD:
            self.setText("Press Space to start the TRAINING Trial using CHORD INPUT!")
        else:
            self.setText("Press Space to start the TRAINING Trial using STANDARD INPUT!")
        return

    ''' Called when the training session finished; Starts the actual test if available '''

    def endTest(self):
        sys.stderr.write("All trials done!")
        if self.testToStart is not None:
            self.testToStart.show()
        self.deleteLater()


class TestLogger(object):
    """
        Responsible for logging user input events and user typing statistics to stdout and/or to a csv file

        @param user_id: The id used to name the resulting csv-files; Used as a logging parameter for later user
        identification
        @param log_to_stdout: Set to True if you want to output the logs to stdout
        @param log_to_file: Set to True if all lines should be written to a csv-file
    """

    def __init__(self, user_id, log_to_stdout, log_to_file):
        super(TestLogger, self).__init__()
        self.log_to_stdout = log_to_stdout
        self.log_to_file = log_to_file
        self.user_id = user_id
        if log_to_file:
            self.init_logging_to_file()

    ''' Creates necessary files for logging and writes appropriate header information '''

    def init_logging_to_file(self):
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

        self.stats_out.writeheader()
        self.events_out.writeheader()
        print("Fields for stats logging: "
              "\"user_id\";\"presented_sentence\";\"transcribed_sentence\";\"text_input_technique\";"
              "\"total_time\";\"wpm\";\"timestamp (ISO)\"")
        print("Fields for event logging: "
              "\"user_id\";\"event_type\";\"event_key\";\"event_text\";\"timestamp (ISO)\"")

    ''' Logs input statistics for a single trial

        @param trial: Current trial object presented in a test
        @param transcribed_text: The text written by the user
        @param time_needed: The time needed to write the whole sentence
        @param wpm: Words per minute ratio
    '''

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

    ''' Logs a keyboard event like pressing/releasing a button

        @param type: The type of the event
        @param key: The key(s) involved in the keyboard event
        @param text: The text received from the input event
    '''

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


class Trial:
    """
        Stores the settings for a single trial of the experiment

        @param text_input_technique: The text input technique. This can be chord input or standard QWERTZ input
        @param text: The sentence the user has to type to complete this trial
    """

    TRAINING_SENTENCES = ["der Mann ging im Herbst mal allein spazieren", "der Junge weiß echt nicht was er tut",
                          "ich hab den Bus verpasst", "das Spiel ist gut schieß nen Punkt",
                          "wir essen zu viel Fleisch iss Gemüse"]

    SENTENCES = ["der Mann ging im Herbst mal allein spazieren", "mein Hund hat dich extrem lieb",
                 "Die Leute mögen dich ich mag dich auch",
                 "der Junge weiß echt nicht was er tut", "ich hab den Bus verpasst", "leider hab ich keine Zeit",
                 "wo rennst du bloß rein", "es war ein Mann ich sehe ihn nicht.", "ich mag ein Eis es ist heiß hier",
                 "geh nun zum Auto es ist kalt hier", "der hat nen Hut aber ich nicht",
                 "das Spiel ist gut schieß nen Punkt", "wir essen zu viel Fleisch iss Gemüse"]

    INPUT_CHORD = "C"
    INPUT_STANDARD = "S"

    def __init__(self, text_input_technique, text):
        self.text_input_technique = text_input_technique
        self.text = text

    ''' Creates a randomized list of trials

        @param conditions: A list of conditions to create appropriate Trials
        @param repetitions: Determines how often a set of sentences is added to the list returned

        @return: A list of Trial objects
    '''

    @staticmethod
    def create_list_from_conditions(conditions, repetitions):
        trials = []
        Trial.SENTENCES = repetitions * Trial.SENTENCES

        for i in range(len(conditions)):
            random.shuffle(Trial.SENTENCES)
            for j in range(len(Trial.SENTENCES)):
                trials.append(Trial(conditions[i], Trial.get_sentence_from_list(len(trials))))
        return trials

    ''' Helper for getting a single sentence from the SENTENCES list

        @param idx: The index of the sentence we want

        @return: The sentence at position idx in the SENTENCES list
    '''

    @staticmethod
    def get_sentence_from_list(idx):
        if idx < len(Trial.SENTENCES):
            return Trial.SENTENCES[idx]
        else:
            return Trial.SENTENCES[len(Trial.SENTENCES) - 1 - idx]

    ''' Get the text the user has to write for this trial'''

    def get_text(self):
        return self.text

    ''' Get the input technique that is used performing this trial'''

    def get_text_input_technique(self):
        return self.text_input_technique

    ''' Creates a list of sentences from the TRAINING_SENTENCES list

        @param input_technique: The input technique used to perform the training
        @param repetitions: Determines how often a set of training sentences is added to the list returned

        @return: A list with Trials for a training session
    '''

    @staticmethod
    def get_training_set(input_technique, repetitions):
        training_trials = []
        Trial.TRAINING_SENTENCES = repetitions * Trial.TRAINING_SENTENCES
        for i in range(len(Trial.TRAINING_SENTENCES)):
            training_trials.append(Trial(input_technique, Trial.TRAINING_SENTENCES[i]))
        return training_trials


def main():
    try:
        app = QtWidgets.QApplication(sys.argv)
        if len(sys.argv) < 2:
            sys.stderr.write("Usage: %s <setup file>\n" % sys.argv[0])
            sys.exit(1)
        if sys.argv[1].endswith('.ini'):
            user_id, conditions = parse_ini_file(sys.argv[1])
        text_training = TextTraining(user_id, "C", TextTest(user_id, conditions))
        sys.exit(app.exec_())
    except Exception:
        print("An error occured!")


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
        conditions = conditions_string.split(";")
    else:
        print("Error: wrong file format.")
        sys.exit(1)
    return user_id, conditions


if __name__ == '__main__':
    main()
