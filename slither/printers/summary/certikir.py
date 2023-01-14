"""
    Module printing summary of the contract using CertiK IR
"""
from typing import List

from slither.printers.summary.slithir import PrinterSlithIR
from slither.core.compilation_unit import SlitherCompilationUnit

class PrinterCertiKIR(PrinterSlithIR):
    ARGUMENT = "certikir"
    HELP = "Print the Certik IR representation of the functions"

    WIKI = "https://github.com/trailofbits/slither/wiki/Printer-documentation#slithir"

    @property
    def compilation_units(self) -> List[SlitherCompilationUnit]:
        return self.slither.certik_compilation_units
