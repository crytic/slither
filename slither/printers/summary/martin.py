"""
    Robert "Uncle Bob" Martin - Agile software metrics
    https://en.wikipedia.org/wiki/Software_package_metrics

    Efferent Coupling (Ce): Number of contracts that the contract depends on
    Afferent Coupling (Ca): Number of contracts that depend on a contract
    Instability (I): Ratio of efferent coupling to total coupling (Ce / (Ce + Ca))
    Abstractness (A): Number of abstract contracts / total number of contracts
    Distance from the Main Sequence (D):  abs(A + I - 1)

"""
from slither.printers.abstract_printer import AbstractPrinter
from slither.utils.martin import MartinMetrics
from slither.utils.output import Output


class Martin(AbstractPrinter):
    ARGUMENT = "martin"
    HELP = "Martin agile software metrics (Ca, Ce, I, A, D)"

    WIKI = "https://github.com/trailofbits/slither/wiki/Printer-documentation#martin"

    def output(self, _filename: str) -> Output:
        if len(self.contracts) == 0:
            return self.generate_output("No contract found")

        martin = MartinMetrics(self.contracts)

        res = self.generate_output(martin.full_text)
        res.add_pretty_table(martin.core.pretty_table, martin.core.title)
        self.info(martin.full_text)
        return res
