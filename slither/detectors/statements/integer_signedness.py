import locale
from slither.core.declarations.solidity_variables import SolidityVariable, SolidityVariableComposed
from slither.slithir.variables import Constant
from slither.slithir.operations import Binary, BinaryType, TypeConversion
from slither.core.solidity_types.elementary_type import ElementaryType, Int, Uint
from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification


def detect_conversions(nodes):
    var = []
    res = []
    flag = 0
    tmp = None

    for node in nodes:
        if flag:
            for ir in node.irs:
                for f in node.internal_calls:
                    if f.name in ["revert()", "revert(string"] :
                        var.remove(tmp)
            flag = 0

        if node.contains_if() or node.contains_require_or_assert():
            for ir in node.irs:
                if isinstance(ir, Binary):
                    if ir.type in (BinaryType.EQUAL, BinaryType.NOT_EQUAL):
                        break

                    (L, R) = ir.read
                    if isinstance(L, Constant) and not isinstance(R, Constant):
                        L = locale.atoi(L.name)
                        if L>=0 and R.type.name in Int:
                            var.append(R)
                            tmp = R
                            flag = 1

                    elif isinstance(R, Constant) and not isinstance(L, Constant):
                        R = locale.atoi(R.name)
                        if R>=0 and L.type.name in Int:
                            var.append(L)
                            tmp = L
                            flag = 1

                    

        for ir in node.irs:
            if isinstance(ir, TypeConversion):
                if isinstance(ir.variable, (Constant, SolidityVariableComposed, SolidityVariable)):
                    continue
                
                if not isinstance(ir.type, ElementaryType):
                    continue

                if ir.type.name in Uint and ir.variable.type.name in Int:
                    if ir.variable not in var:
                        res.append(node)
                        continue


    return res    


class Signdness(AbstractDetector):
    """
    Documentation
    """

    ARGUMENT = 'signedness' # slither will launch the detector with slither.py --detect mydetector
    HELP = 'Integer signedness'
    IMPACT = DetectorClassification.LOW
    CONFIDENCE = DetectorClassification.HIGH

    # region wiki
    WIKI = 'https://github.com/crytic/slither/wiki/Detector-Documentation#interger_signedness'
    WIKI_TITLE = 'Integer Signedness'
    WIKI_DESCRIPTION = 'Casting a negative integer to an unsigned integer results in an error and does not throw an exception.'
    WIKI_EXPLOIT_SCENARIO = """
```solidity


```
"""
    WIKI_RECOMMENDATION = 'Avoid such conversions'
    # endregion wiki

    def _detect(self):
        results = []
        for c in self.contracts:
            conversions = []

            for f in c.functions_declared:

                f_results = detect_conversions(f.nodes)

                if f_results:
                     conversions.append((f, f_results))

            if conversions:
                for (func, nodes) in conversions:
                    info = [
                        func,
                        "It may cause data loss or misinterpretation.\n",
                    ]

                    nodes.sort(key=lambda x: x.node_id)

                    for node in nodes:
                        info += ["\t-", node, "\n"]

                    res = self.generate_result(info)
                    results.append(res)

        return results
