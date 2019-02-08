"""
    Module printing summary of the contract
"""

from slither.printers.abstract_printer import AbstractPrinter
from slither.utils.colors import blue, green, magenta

class PrinterSlithIRSSA(AbstractPrinter):

    ARGUMENT = 'slithir-ssa'
    HELP = 'Print the slithIR representation of the functions'

    WIKI = 'https://github.com/trailofbits/slither/wiki/Printer-documentation#slithir-ssa'

    def output(self, _filename):
        """
            _filename is not used
            Args:
                _filename(string)
        """

        txt = ""
        for contract in self.contracts:
            print('Contract {}'.format(contract.name))
            for function in contract.functions:
                if function.contract == contract:
                    print('\tFunction {}'.format(function.full_name))
                    for node in function.nodes:
                        if node.expression:
                            print('\t\tExpression: {}'.format(node.expression))
                        if node.irs_ssa:
                            print('\t\tIRs:')
                            for ir in node.irs_ssa:
                                print('\t\t\t{}'.format(ir))
            for modifier in contract.modifiers:
                if modifier.contract == contract:
                    print('\tModifier {}'.format(modifier.full_name))
                    for node in modifier.nodes:
                        print(node)
                        if node.expression:
                            print('\t\tExpression: {}'.format(node.expression))
                        if node.irs_ssa:
                            print('\t\tIRs:')
                            for ir in node.irs_ssa:
                                print('\t\t\t{}'.format(ir))
        self.info(txt)
