import abc
import re

from slither.utils.colors import green, yellow, red


class IncorrectDetectorInitialization(Exception):
    pass


class DetectorClassification:
    LOW = 0
    MEDIUM = 1
    HIGH = 2
    CODE_QUALITY = 3


classification_colors = {
    DetectorClassification.CODE_QUALITY: green,
    DetectorClassification.LOW: green,
    DetectorClassification.MEDIUM: yellow,
    DetectorClassification.HIGH: red,
}


class AbstractDetector(metaclass=abc.ABCMeta):
    ARGUMENT = ''  # run the detector with slither.py --ARGUMENT
    HELP = ''  # help information
    CLASSIFICATION = None

    HIDDEN_DETECTOR = False  # yes if the detector should not be showed

    def __init__(self, slither, logger):
        self.slither = slither
        self.contracts = slither.contracts
        self.filename = slither.filename
        self.logger = logger

        if not self.HELP:
            raise IncorrectDetectorInitialization('HELP is not initialized')

        if not self.ARGUMENT:
            raise IncorrectDetectorInitialization('ARGUMENT is not initialized')

        if re.match('^[a-zA-Z0-9_-]*$', self.ARGUMENT) is None:
            raise IncorrectDetectorInitialization('ARGUMENT has illegal character')

        if self.CLASSIFICATION not in [DetectorClassification.LOW,
                                       DetectorClassification.MEDIUM,
                                       DetectorClassification.HIGH,
                                       DetectorClassification.CODE_QUALITY]:
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
        return classification_colors[self.CLASSIFICATION]
