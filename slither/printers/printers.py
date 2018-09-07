import sys, inspect
import logging

from slither.printers.abstractPrinter import AbstractPrinter

# Printer must be imported here
from slither.printers.summary.printerSummary import PrinterSummary
from slither.printers.summary.printerQuickSummary import PrinterQuickSummary
from slither.printers.inheritance.printerInheritance import PrinterInheritance
from slither.printers.functions.authorization import PrinterWrittenVariablesAndAuthorization

logger_printer = logging.getLogger("Printers")

class Printers(object):

    def __init__(self):
        self.printers = {}
        self._load_printers()

    def _load_printers(self):
        for name, obj in inspect.getmembers(sys.modules[__name__]):
            if inspect.isclass(obj):
                if issubclass(obj, AbstractPrinter) and name != 'AbstractPrinter':
                    if name in self.printers:
                        raise Exception('Printer name collision: {}'.format(name))
                    self.printers[name] = obj

    def run_printer(self, slither, name):
        Printer = self.printers[name]
        instance = Printer(slither, logger_printer)
        return instance.output(slither.filename)
