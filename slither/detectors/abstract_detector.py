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
    OPTIMIZATION = 4


classification_colors = {
    DetectorClassification.INFORMATIONAL: green,
    DetectorClassification.OPTIMIZATION: green,
    DetectorClassification.LOW: green,
    DetectorClassification.MEDIUM: yellow,
    DetectorClassification.HIGH: red
}

classification_txt = {
    DetectorClassification.INFORMATIONAL: 'Informational',
    DetectorClassification.OPTIMIZATION: 'Optimization',
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

        if not self.WIKI_EXPLOIT_SCENARIO and self.IMPACT not in [DetectorClassification.INFORMATIONAL,
                                                                      DetectorClassification.OPTIMIZATION]:
            raise IncorrectDetectorInitialization('WIKI_EXPLOIT_SCENARIO is not initialized {}'.format(self.__class__.__name__))

        if not self.WIKI_RECOMMENDATION:
            raise IncorrectDetectorInitialization('WIKI_RECOMMENDATION is not initialized {}'.format(self.__class__.__name__))

        if re.match('^[a-zA-Z0-9_-]*$', self.ARGUMENT) is None:
            raise IncorrectDetectorInitialization('ARGUMENT has illegal character {}'.format(self.__class__.__name__))

        if self.IMPACT not in [DetectorClassification.LOW,
                                       DetectorClassification.MEDIUM,
                                       DetectorClassification.HIGH,
                                       DetectorClassification.INFORMATIONAL,
                                       DetectorClassification.OPTIMIZATION]:
            raise IncorrectDetectorInitialization('IMPACT is not initialized {}'.format(self.__class__.__name__))

        if self.CONFIDENCE not in [DetectorClassification.LOW,
                                       DetectorClassification.MEDIUM,
                                       DetectorClassification.HIGH,
                                       DetectorClassification.INFORMATIONAL,
                                       DetectorClassification.OPTIMIZATION]:
            raise IncorrectDetectorInitialization('CONFIDENCE is not initialized {}'.format(self.__class__.__name__))


    def _log(self, info):
        self.logger.info(self.color(info))

    @abc.abstractmethod
    def _detect(self):
        """TODO Documentation"""
        return

    def detect(self):
        all_results = self._detect()
        results = []
        # only keep valid result, and remove dupplicate
        [results.append(r) for r in all_results if self.slither.valid_result(r) and r not in results]
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

    def generate_json_result(self, info, additional_fields={}):
        d = OrderedDict()
        d['check'] = self.ARGUMENT
        d['impact'] = classification_txt[self.IMPACT]
        d['confidence'] = classification_txt[self.CONFIDENCE]
        d['description'] = info
        d['elements'] = []
        if additional_fields:
            d['additional_fields'] = additional_fields
        return d

    @staticmethod
    def _create_base_element(type, name, source_mapping, type_specific_fields={}, additional_fields={}):
        element = {'type': type,
                   'name': name,
                   'source_mapping': source_mapping}
        if type_specific_fields:
            element['type_specific_fields'] = type_specific_fields
        if additional_fields:
            element['additional_fields'] = additional_fields
        return element

    @staticmethod
    def _create_parent_element(element):
        from slither.core.children.child_contract import ChildContract
        from slither.core.children.child_function import ChildFunction
        from slither.core.children.child_inheritance import ChildInheritance
        if isinstance(element, ChildInheritance):
            if element.contract_declarer:
                contract = {'elements': []}
                AbstractDetector.add_contract_to_json(element.contract_declarer, contract)
                return contract['elements'][0]
        elif isinstance(element, ChildContract):
            if element.contract:
                contract = {'elements': []}
                AbstractDetector.add_contract_to_json(element.contract, contract)
                return contract['elements'][0]
        elif isinstance(element, ChildFunction):
            if element.function:
                function = {'elements': []}
                AbstractDetector.add_function_to_json(element.function, function)
                return function['elements'][0]
        return None

    @staticmethod
    def add_variable_to_json(variable, d, additional_fields={}):
        type_specific_fields = {
            'parent': AbstractDetector._create_parent_element(variable)
        }
        element = AbstractDetector._create_base_element('variable',
                                                        variable.name,
                                                        variable.source_mapping,
                                                        type_specific_fields,
                                                        additional_fields)
        d['elements'].append(element)

    @staticmethod
    def add_variables_to_json(variables, d):
        for variable in sorted(variables, key=lambda x:x.name):
            AbstractDetector.add_variable_to_json(variable, d)

    @staticmethod
    def add_contract_to_json(contract, d, additional_fields={}):
        element = AbstractDetector._create_base_element('contract',
                                                        contract.name,
                                                        contract.source_mapping,
                                                        {},
                                                        additional_fields)
        d['elements'].append(element)

    @staticmethod
    def add_function_to_json(function, d, additional_fields={}):
        type_specific_fields = {
            'parent': AbstractDetector._create_parent_element(function),
            'signature': function.full_name
        }
        element = AbstractDetector._create_base_element('function',
                                                        function.name,
                                                        function.source_mapping,
                                                        type_specific_fields,
                                                        additional_fields)
        d['elements'].append(element)


    @staticmethod
    def add_functions_to_json(functions, d, additional_fields={}):
        for function in sorted(functions, key=lambda x: x.name):
            AbstractDetector.add_function_to_json(function, d, additional_fields)

    @staticmethod
    def add_enum_to_json(enum, d, additional_fields={}):
        type_specific_fields = {
            'parent': AbstractDetector._create_parent_element(enum)
        }
        element = AbstractDetector._create_base_element('enum',
                                                        enum.name,
                                                        enum.source_mapping,
                                                        type_specific_fields,
                                                        additional_fields)
        d['elements'].append(element)

    @staticmethod
    def add_struct_to_json(struct, d, additional_fields={}):
        type_specific_fields = {
            'parent': AbstractDetector._create_parent_element(struct)
        }
        element = AbstractDetector._create_base_element('struct',
                                                        struct.name,
                                                        struct.source_mapping,
                                                        type_specific_fields,
                                                        additional_fields)
        d['elements'].append(element)

    @staticmethod
    def add_event_to_json(event, d, additional_fields={}):
        type_specific_fields = {
            'parent': AbstractDetector._create_parent_element(event),
            'signature': event.full_name
        }
        element = AbstractDetector._create_base_element('event',
                                                        event.name,
                                                        event.source_mapping,
                                                        type_specific_fields,
                                                        additional_fields)

        d['elements'].append(element)

    @staticmethod
    def add_node_to_json(node, d, additional_fields={}):
        type_specific_fields = {
            'parent': AbstractDetector._create_parent_element(node),
        }
        node_name = str(node.expression) if node.expression else ""
        element = AbstractDetector._create_base_element('node',
                                                        node_name,
                                                        node.source_mapping,
                                                        type_specific_fields,
                                                        additional_fields)
        d['elements'].append(element)


    @staticmethod
    def add_nodes_to_json(nodes, d):
        for node in sorted(nodes, key=lambda x: x.node_id):
            AbstractDetector.add_node_to_json(node, d)

    @staticmethod
    def add_pragma_to_json(pragma, d, additional_fields={}):
        type_specific_fields = {
            'directive': pragma.directive
        }
        element = AbstractDetector._create_base_element('pragma',
                                                        pragma.version,
                                                        pragma.source_mapping,
                                                        type_specific_fields,
                                                        additional_fields)

        d['elements'].append(element)
