"""
    Module printing summary of the contract
"""

from slither.printers.abstract_printer import AbstractPrinter


class PrinterSlithIRSSA(AbstractPrinter):

    ARGUMENT = "slithir-ssa"
    HELP = "Print the slithIR representation of the functions"

    WIKI = "https://github.com/trailofbits/slither/wiki/Printer-documentation#slithir-ssa"

    def output(self, _filename):
        """
        _filename is not used
        Args:
            _filename(string)
        """

        txt = ""
        for contract in self.contracts:
            txt += f"Contract {contract.name}" + "\n"
            for function in contract.functions:
                txt += f"\tFunction {function.canonical_name}" + "\n"
                for node in function.nodes:
                    if node.expression:
                        txt += f"\t\tExpression: {node.expression}" + "\n"
                    if node.irs_ssa:
                        txt += "\t\tIRs:" + "\n"
                        for ir in node.irs_ssa:
                            txt += f"\t\t\t{ir}" + "\n"
            for modifier in contract.modifiers:
                txt += f"\tModifier {modifier.canonical_name}" + "\n"
                for node in modifier.nodes:
                    txt += str(node) + "\n"
                    if node.expression:
                        txt += f"\t\tExpression: {node.expression}" + "\n"
                    if node.irs_ssa:
                        txt += "\t\tIRs:" + "\n"
                        for ir in node.irs_ssa:
                            txt += f"\t\t\t{ir}" + "\n"
        self.info(txt)
        res = self.generate_output(txt)
        return res
