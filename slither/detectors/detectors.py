import sys, inspect
import os
import logging

from slither.detectors.abstractDetector import AbstractDetector
from slither.detectors.detectorClassification import DetectorClassification

# Detectors must be imported here
from slither.detectors.examples.backdoor import Backdoor
from slither.detectors.variables.uninitializedStateVarsDetection import UninitializedStateVarsDetection

###

logger_detector = logging.getLogger("Detectors")

class Detectors:

    def __init__(self):
        self.detectors = {}
        self.low = []
        self.medium = []
        self.high = []

        self._load_detectors()

    def _load_detectors(self):
        for name, obj in inspect.getmembers(sys.modules[__name__]):
            if inspect.isclass(obj):
                if issubclass(obj, AbstractDetector) and name != 'AbstractDetector':
                    if obj.HIDDEN_DETECTOR:
                        continue
                    if name in self.detectors:
                        raise Exception('Detector name collision: {}'.format(name))
                    self.detectors[name] = obj
                    if obj.CLASSIFICATION == DetectorClassification.LOW:
                        self.low.append(name)
                    elif obj.CLASSIFICATION == DetectorClassification.MEDIUM:
                        self.medium.append(name)
                    elif obj.CLASSIFICATION == DetectorClassification.HIGH:
                        self.high.append(name)
                    else:
                        raise Exception('Unknown classification')

    def run_detector(self, slither, name):
        Detector = self.detectors[name]
        instance = Detector(slither, logger_detector)
        return instance.detect()
