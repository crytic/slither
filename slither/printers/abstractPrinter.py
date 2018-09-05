import abc

class IncorrectPrinterInitialization(Exception):
    pass

class AbstractPrinter(object):
    __metaclass__ = abc.ABCMeta

    ARGUMENT = '' # run the printer with slither.py --ARGUMENT
    HELP = '' # help information

    def __init__(self, slither, logger):
        self.slither = slither
        self.contracts = slither.contracts
        self.filename = slither.filename
        self.logger = logger
        if self.HELP == '':
            raise IncorrectPrinterInitialization('HELP is not initialized')
        if self.ARGUMENT == '':
            raise IncorrectPrinterInitialization('ARGUMENT is not initialized')

    def info(self, info):
        if self.logger:
            self.logger.info(info)

    @abc.abstractmethod
    def output(self, filename):
        """TODO Documentation"""
        return
