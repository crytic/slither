"""
    Module printing summary of the contract
"""
from slither.core.declarations import Function
from slither.printers.abstract_printer import AbstractPrinter
from typing import List
from slither.core.compilation_unit import SlitherCompilationUnit

def _print_function(function: Function) -> str:
    txt = ""
    for node in function.nodes:
        if node.expression:
            txt += f"\t\tExpression: {node.expression}\n"
            txt += "\t\tIRs:\n"
            for ir in node.irs:
                txt += f"\t\t\t{ir}\n"
        elif node.irs:
            txt += "\t\tIRs:\n"
            for ir in node.irs:
                txt += f"\t\t\t{ir}\n"
    return txt


class PrinterSlithIR(AbstractPrinter):
    ARGUMENT = "slithir"
    HELP = "Print the slithIR representation of the functions"

    WIKI = "https://github.com/trailofbits/slither/wiki/Printer-documentation#slithir"

    @property
    def compilation_units(self) -> List[SlitherCompilationUnit]:
        """
        List of compilation units to print the IR for
        """
        return self.slither.compilation_units

    def output(self, _filename):
        """
        _filename is not used
        Args:
            _filename(string)
        """

        txt = ""
        for compilation_unit in self.compilation_units:
            for contract in compilation_unit.contracts:
                if contract.is_top_level:
                    continue
                txt += f"Contract {contract.name}\n"
                for function in contract.functions:
                    txt += f'\tFunction {function.canonical_name} {"" if function.is_shadowed else "(*)"}\n'
                    txt += _print_function(function)
                for modifier in contract.modifiers:
                    txt += f"\tModifier {modifier.canonical_name}\n"
                    txt += _print_function(modifier)
            if compilation_unit.functions_top_level:
                txt += "Top level functions"
            for function in compilation_unit.functions_top_level:
                txt += f"\tFunction {function.canonical_name}\n"
                txt += _print_function(function)
        self.info(txt)
        res = self.generate_output(txt)
        return res
