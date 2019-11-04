"""
    Module printing summary of the contract
"""

from slither.printers.abstract_printer import AbstractPrinter

class PrinterSlithIR(AbstractPrinter):

    ARGUMENT = 'slithir'
    HELP = 'Print the slithIR representation of the functions'

    WIKI = 'https://github.com/trailofbits/slither/wiki/Printer-documentation#slithir'

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
                print(f'\tFunction {function.canonical_name} {"" if function.is_shadowed else "(*)"}')
                for node in function.nodes:
                    if node.expression:
                        print('\t\tExpression: {}'.format(node.expression))
                        print('\t\tIRs:')
                        for ir in node.irs:
                            print('\t\t\t{}'.format(ir))
                    elif node.irs:
                        print('\t\tIRs:')
                        for ir in node.irs:
                            print('\t\t\t{}'.format(ir))
                for modifier_statement in function.modifiers_statements:
                    print(f'\t\tModifier Call {modifier_statement.entry_point.expression}')
                for modifier_statement in function.explicit_base_constructor_calls_statements:
                    print(f'\t\tConstructor Call {modifier_statement.entry_point.expression}')
            for modifier in contract.modifiers:
                print('\tModifier {}'.format(modifier.canonical_name))
                for node in modifier.nodes:
                    print(node)
                    if node.expression:
                        print('\t\tExpression: {}'.format(node.expression))
                        print('\t\tIRs:')
                        for ir in node.irs:
                            print('\t\t\t{}'.format(ir))
        self.info(txt)
