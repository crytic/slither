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
            txt += 'Contract {}'.format(contract.name)
            for function in contract.functions:
                txt += f'\tFunction {function.canonical_name} {"" if function.is_shadowed else "(*)"}'
                for node in function.nodes:
                    if node.expression:
                        txt += '\t\tExpression: {}'.format(node.expression)
                        txt += '\t\tIRs:'
                        for ir in node.irs:
                            txt += '\t\t\t{}'.format(ir)
                    elif node.irs:
                        txt += '\t\tIRs:'
                        for ir in node.irs:
                            txt += '\t\t\t{}'.format(ir)
                for modifier_statement in function.modifiers_statements:
                    txt += f'\t\tModifier Call {modifier_statement.entry_point.expression}'
                for modifier_statement in function.explicit_base_constructor_calls_statements:
                    txt += f'\t\tConstructor Call {modifier_statement.entry_point.expression}'
            for modifier in contract.modifiers:
                txt += '\tModifier {}'.format(modifier.canonical_name)
                for node in modifier.nodes:
                    txt += str(node)
                    if node.expression:
                        txt += '\t\tExpression: {}'.format(node.expression)
                        txt += '\t\tIRs:'
                        for ir in node.irs:
                            txt += '\t\t\t{}'.format(ir)
        self.info(txt)
        res = self.generate_output(txt)
        return res
