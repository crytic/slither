import abc

from slither.utils import json_utils


class IncorrectPrinterInitialization(Exception):
    pass


class AbstractPrinter(metaclass=abc.ABCMeta):
    ARGUMENT = ''  # run the printer with slither.py --ARGUMENT
    HELP = ''  # help information

    WIKI = ''

    def __init__(self, slither, logger):
        self.slither = slither
        self.contracts = slither.contracts
        self.filename = slither.filename
        self.logger = logger

        if not self.HELP:
            raise IncorrectPrinterInitialization('HELP is not initialized {}'.format(self.__class__.__name__))

        if not self.ARGUMENT:
            raise IncorrectPrinterInitialization('ARGUMENT is not initialized {}'.format(self.__class__.__name__))

        if not self.WIKI:
            raise IncorrectPrinterInitialization('WIKI is not initialized {}'.format(self.__class__.__name__))

    def info(self, info):
        if self.logger:
            self.logger.info(info)


    def generate_json_result(self, info, additional_fields=None):
        if additional_fields is None:
            additional_fields = {}
        d = json_utils.generate_json_result(info, additional_fields)
        d['printer'] = self.ARGUMENT

        return d

    @staticmethod
    def add_contract_to_json(e, d, additional_fields=None):
        json_utils.add_contract_to_json(e, d, additional_fields=additional_fields)

    @staticmethod
    def add_function_to_json(e, d, additional_fields=None):
        json_utils.add_function_to_json(e, d, additional_fields=additional_fields)

    @staticmethod
    def add_functions_to_json(e, d, additional_fields=None):
        json_utils.add_functions_to_json(e, d, additional_fields=additional_fields)

    @staticmethod
    def add_file_to_json(e, content, d, additional_fields=None):
        json_utils.add_file_to_json(e, content, d, additional_fields)

    @staticmethod
    def add_pretty_table_to_json(e, content, d, additional_fields=None):
        json_utils.add_pretty_table_to_json(e, content, d, additional_fields)

    @staticmethod
    def add_other_to_json(name, source_mapping, d, slither, additional_fields=None):
        json_utils.add_other_to_json(name, source_mapping, d, slither, additional_fields)

    @abc.abstractmethod
    def output(self, filename):
        """TODO Documentation"""
        return
