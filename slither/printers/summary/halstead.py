"""
    Halstead complexity metrics
    https://en.wikipedia.org/wiki/Halstead_complexity_measures

    12 metrics based on the number of unique operators and operands:

    Core metrics:
    n1 = the number of distinct operators
    n2 = the number of distinct operands
    N1 = the total number of operators
    N2 = the total number of operands

    Extended metrics1:
    n = n1 + n2  # Program vocabulary
    N = N1 + N2  # Program length
    S = n1 * log2(n1) + n2 * log2(n2) # Estimated program length
    V = N * log2(n) # Volume

    Extended metrics2:
    D = (n1 / 2) * (N2 / n2) # Difficulty
    E = D * V # Effort
    T = E / 18 seconds # Time required to program
    B = (E^(2/3)) / 3000 # Number of delivered bugs

"""
from slither.printers.abstract_printer import AbstractPrinter
from slither.utils.halstead import HalsteadMetrics
from slither.utils.output import Output


class Halstead(AbstractPrinter):
    ARGUMENT = "halstead"
    HELP = "Computes the Halstead complexity metrics for each contract"

    WIKI = "https://github.com/trailofbits/slither/wiki/Printer-documentation#halstead"

    def output(self, _filename: str) -> Output:
        if len(self.contracts) == 0:
            return self.generate_output("No contract found")

        halstead = HalsteadMetrics(self.contracts)

        res = self.generate_output(halstead.full_text)
        res.add_pretty_table(halstead.core.pretty_table, halstead.core.title)
        res.add_pretty_table(halstead.extended1.pretty_table, halstead.extended1.title)
        res.add_pretty_table(halstead.extended2.pretty_table, halstead.extended2.title)
        self.info(halstead.full_text)

        return res
