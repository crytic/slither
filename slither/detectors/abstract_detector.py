import abc
import re

from slither.utils.colors import green, yellow, red

from collections import OrderedDict

class IncorrectDetectorInitialization(Exception):
    pass


class DetectorClassification:
    HIGH = 0
    MEDIUM = 1
    LOW = 2
    INFORMATIONAL = 3


classification_colors = {
    DetectorClassification.INFORMATIONAL: green,
    DetectorClassification.LOW: green,
    DetectorClassification.MEDIUM: yellow,
    DetectorClassification.HIGH: red,
}

classification_txt = {
    DetectorClassification.INFORMATIONAL: 'Informational',
    DetectorClassification.LOW: 'Low',
    DetectorClassification.MEDIUM: 'Medium',
    DetectorClassification.HIGH: 'High',
}

class AbstractDetector(metaclass=abc.ABCMeta):
    ARGUMENT = ''  # run the detector with slither.py --ARGUMENT
    HELP = ''  # help information
    IMPACT = None
    CONFIDENCE = None

    WIKI = ''

    def __init__(self, slither, logger):
        self.slither = slither
        self.contracts = slither.contracts
        self.filename = slither.filename
        self.logger = logger

        if not self.HELP:
            raise IncorrectDetectorInitialization('HELP is not initialized {}'.format(self.__class__.__name__))

        if not self.ARGUMENT:
            raise IncorrectDetectorInitialization('ARGUMENT is not initialized {}'.format(self.__class__.__name__))

        if re.match('^[a-zA-Z0-9_-]*$', self.ARGUMENT) is None:
            raise IncorrectDetectorInitialization('ARGUMENT has illegal character {}'.format(self.__class__.__name__))

        if self.IMPACT not in [DetectorClassification.LOW,
                                       DetectorClassification.MEDIUM,
                                       DetectorClassification.HIGH,
                                       DetectorClassification.INFORMATIONAL]:
            raise IncorrectDetectorInitialization('IMPACT is not initialized {}'.format(self.__class__.__name__))

        if self.CONFIDENCE not in [DetectorClassification.LOW,
                                       DetectorClassification.MEDIUM,
                                       DetectorClassification.HIGH,
                                       DetectorClassification.INFORMATIONAL]:
            raise IncorrectDetectorInitialization('CONFIDENCE is not initialized {}'.format(self.__class__.__name__))

    def log(self, info):
        if self.logger:
            info = "\n"+info
            if self.WIKI != '':
                info += 'Reference: {}'.format(self.WIKI)
            self.logger.info(self.color(info))

    @abc.abstractmethod
    def detect(self):
        """TODO Documentation"""
        return

    @property
    def color(self):
        return classification_colors[self.IMPACT]

    def generate_json_result(self, info):
        d = OrderedDict()
        d['check'] = self.ARGUMENT
        d['impact'] = classification_txt[self.IMPACT]
        d['confidence'] = classification_txt[self.CONFIDENCE]
        d['description'] = info
        return d

    @staticmethod
    def add_variable_to_json(variable, d):
        assert 'variable' not in d
        d['variable'] = {'name': variable.name, 'source_mapping': variable.source_mapping}

    @staticmethod
    def add_variables_to_json(variables, d):
        assert 'variables' not in d
        d['variables'] = [{'name': variable.name,
                           'source_mapping': variable.source_mapping}
                          for variable in variables]

    @staticmethod
    def add_contract_to_json(contract, d):
        assert 'contract' not in d
        d['contract'] = {'name': contract.name, 'source_mapping': contract.source_mapping}

    @staticmethod
    def add_function_to_json(function, d):
        assert 'function' not in d
        contract = dict()
        AbstractDetector.add_contract_to_json(function.contract, contract)
        d['function'] = {'name': function.name, 'source_mapping': function.source_mapping, 'contract': contract['contract']}

    @staticmethod
    def add_functions_to_json(functions, d):
        assert 'functions' not in d
        d['functions'] = []
        for function in functions:
            func_dict = dict()
            AbstractDetector.add_function_to_json(function, func_dict)
            d['functions'].append(func_dict['function'])

    @staticmethod
    def add_nodes_to_json(nodes, d):
        assert 'expressions' not in d
        d['expressions'] = [{'expression': str(node.expression),
                             'source_mapping': node.source_mapping}
                            for node in nodes]
