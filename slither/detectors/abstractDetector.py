import abc
import re
from slither.detectors.detectorClassification import DetectorClassification
from slither.utils.colors import green, yellow, red

class IncorrectDetectorInitialization(Exception):
    pass

class AbstractDetector(object, metaclass=abc.ABCMeta):
    ARGUMENT = '' # run the detector with slither.py --ARGUMENT
    HELP = '' # help information
    CLASSIFICATION = None

    HIDDEN_DETECTOR = False # yes if the detector should not be showed

    def __init__(self, slither, logger):
        self.slither = slither
        self.contracts = slither.contracts
        self.filename = slither.filename
        self.logger = logger
        if self.HELP == '':
            raise IncorrectDetectorInitialization('HELP is not initialized')
        if self.ARGUMENT == '':
            raise IncorrectDetectorInitialization('ARGUMENT is not initialized')
        if re.match('^[a-zA-Z0-9_-]*$', self.ARGUMENT) is None:
            raise IncorrectDetectorInitialization('ARGUMENT has illegal character')
        if not self.CLASSIFICATION in [DetectorClassification.LOW,
                                       DetectorClassification.MEDIUM,
                                       DetectorClassification.HIGH]:
            raise IncorrectDetectorInitialization('CLASSIFICATION is not initialized')

    def log(self, info):
        if self.logger:
            self.logger.info(self.color(info))

    @abc.abstractmethod
    def detect(self):
        """TODO Documentation"""
        return

    @property
    def color(self):
        if self.CLASSIFICATION == DetectorClassification.LOW:
            return green
        if self.CLASSIFICATION == DetectorClassification.MEDIUM:
            return yellow
        if self.CLASSIFICATION == DetectorClassification.HIGH:
            return red
