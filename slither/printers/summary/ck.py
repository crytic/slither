"""
    CK Metrics are a suite of six software metrics proposed by Chidamber and Kemerer in 1994.
    These metrics are used to measure the complexity of a class.
    https://en.wikipedia.org/wiki/Programming_complexity

    - Response For a Class (RFC) is a metric that measures the number of unique method calls within a class.
    - Number of Children (NOC) is a metric that measures the number of children a class has.
    - Depth of Inheritance Tree (DIT) is a metric that measures the number of parent classes a class has.
    - Coupling Between Object Classes (CBO) is a metric that measures the number of classes a class is coupled to.

    Not implemented:
    - Lack of Cohesion of Methods (LCOM) is a metric that measures the lack of cohesion in methods.
    - Weighted Methods per Class (WMC) is a metric that measures the complexity of a class.

    During the calculation of the metrics above, there are a number of other intermediate metrics that are calculated.
    These are also included in the output:
     - State variables: total number of state variables
     - Constants: total number of constants
     - Immutables: total number of immutables
     - Public: total number of public functions
     - External: total number of external functions
     - Internal: total number of internal functions
     - Private: total number of private functions
     - Mutating: total number of state mutating functions
     - View: total number of view functions
     - Pure: total number of pure functions
     - External mutating: total number of external mutating functions
     - No auth or onlyOwner: total number of functions without auth or onlyOwner modifiers
     - No modifiers: total number of functions without modifiers
     - Ext calls: total number of external calls

"""
from slither.printers.abstract_printer import AbstractPrinter
from slither.utils.ck import CKMetrics
from slither.utils.output import Output


class CK(AbstractPrinter):
    ARGUMENT = "ck"
    HELP = "Chidamber and Kemerer (CK) complexity metrics and related function attributes"

    WIKI = "https://github.com/trailofbits/slither/wiki/Printer-documentation#ck"

    def output(self, _filename: str) -> Output:
        if len(self.contracts) == 0:
            return self.generate_output("No contract found")

        ck = CKMetrics(self.contracts)

        res = self.generate_output(ck.full_text)
        res.add_pretty_table(ck.auxiliary1.pretty_table, ck.auxiliary1.title)
        res.add_pretty_table(ck.auxiliary2.pretty_table, ck.auxiliary2.title)
        res.add_pretty_table(ck.auxiliary3.pretty_table, ck.auxiliary3.title)
        res.add_pretty_table(ck.auxiliary4.pretty_table, ck.auxiliary4.title)
        res.add_pretty_table(ck.core.pretty_table, ck.core.title)
        self.info(ck.full_text)

        return res
