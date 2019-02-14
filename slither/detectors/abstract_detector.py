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

    WIKI_TITLE = ''
    WIKI_DESCRIPTION = ''
    WIKI_EXPLOIT_SCENARIO = ''
    WIKI_RECOMMENDATION = ''


    def __init__(self, slither, logger):
        self.slither = slither
        self.contracts = slither.contracts
        self.filename = slither.filename
        self.logger = logger

        if not self.HELP:
            raise IncorrectDetectorInitialization('HELP is not initialized {}'.format(self.__class__.__name__))

        if not self.ARGUMENT:
            raise IncorrectDetectorInitialization('ARGUMENT is not initialized {}'.format(self.__class__.__name__))

        if not self.WIKI:
            raise IncorrectDetectorInitialization('WIKI is not initialized {}'.format(self.__class__.__name__))

        if not self.WIKI_TITLE:
            raise IncorrectDetectorInitialization('WIKI_TITLE is not initialized {}'.format(self.__class__.__name__))

        if not self.WIKI_DESCRIPTION:
            raise IncorrectDetectorInitialization('WIKI_DESCRIPTION is not initialized {}'.format(self.__class__.__name__))

        if not self.WIKI_EXPLOIT_SCENARIO and self.IMPACT != DetectorClassification.INFORMATIONAL:
            raise IncorrectDetectorInitialization('WIKI_EXPLOIT_SCENARIO is not initialized {}'.format(self.__class__.__name__))

        if not self.WIKI_RECOMMENDATION:
            raise IncorrectDetectorInitialization('WIKI_RECOMMENDATION is not initialized {}'.format(self.__class__.__name__))

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

#    def log(self, info):
#        if self.logger:
#            info = "\n"+info
#            if self.WIKI != '':
#                info += 'Reference: {}'.format(self.WIKI)
#            self.logger.info(self.color(info))

    def _log(self, info):
        self.logger.info(self.color(info))

    @abc.abstractmethod
    def _detect(self):
        """TODO Documentation"""
        return

    def detect(self):
        results = self._detect()
        results = [r for r in results if self.slither.valid_result(r)]
        if results:
            if self.logger:
                info = '\n'
                for idx, result in enumerate(results):
                    if self.slither.triage_mode:
                        info += '{}: '.format(idx)
                    info += result['description']
                info += 'Reference: {}'.format(self.WIKI)
                self._log(info)
        if results and self.slither.triage_mode:
            while True:
                indexes = input('Results to hide during next runs: "0,1,..." or "All" (enter to not hide results): '.format(len(results)))
                if indexes == 'All':
                    self.slither.save_results_to_hide(results)
                    return []
                if indexes == '':
                    return results
                if indexes.startswith('['):
                    indexes = indexes[1:]
                if indexes.endswith(']'):
                    indexes = indexes[:-1]
                try:
                    indexes = [int(i) for i in indexes.split(',')]
                    self.slither.save_results_to_hide([r for (idx, r) in enumerate(results) if idx in indexes])
                    return [r for (idx, r) in enumerate(results) if idx not in indexes]
                except ValueError:
                    self.logger.error(yellow('Malformed input. Example of valid input: 0,1,2,3'))
        return results


    @property
    def color(self):
        return classification_colors[self.IMPACT]

    def generate_json_result(self, info):
        d = OrderedDict()
        d['check'] = self.ARGUMENT
        d['impact'] = classification_txt[self.IMPACT]
        d['confidence'] = classification_txt[self.CONFIDENCE]
        d['description'] = info
        d['elements'] = []
        return d

    @staticmethod
    def add_variable_to_json(variable, d):
        d['elements'].append({'type': 'variable',
                              'name': variable.name,
                              'source_mapping': variable.source_mapping})

    @staticmethod
    def add_variables_to_json(variables, d):
        for variable in sorted(variables, key=lambda x:x.name):
            AbstractDetector.add_variable_to_json(variable, d)

    @staticmethod
    def add_contract_to_json(contract, d):
        d['elements'].append({'type': 'contract',
                              'name': contract.name,
                              'source_mapping': contract.source_mapping})

    @staticmethod
    def add_function_to_json(function, d):
        contract = {'elements':[]}
        AbstractDetector.add_contract_to_json(function.contract, contract)
        d['elements'].append({'type': 'function',
                              'name': function.name,
                              'source_mapping': function.source_mapping,
                              'contract': contract['elements'][0]})

    @staticmethod
    def add_functions_to_json(functions, d):
        for function in sorted(functions, key=lambda x: x.name):
            AbstractDetector.add_function_to_json(function, d)

    @staticmethod
    def add_nodes_to_json(nodes, d):
        for node in sorted(nodes, key=lambda x: x.node_id):
            d['elements'].append({'type': 'expression',
                                  'expression': str(node.expression),
                                  'source_mapping': node.source_mapping})

