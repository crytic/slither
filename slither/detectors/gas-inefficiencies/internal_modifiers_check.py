from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification
from slither.slithir.operations import Operation

class InternalModifierCheck(AbstractDetector):
    """
    Place require statements into internal virtual functions for smaller contract size.
    """

    ARGUMENT = "internal-modifier-check"
    HELP = "Place require statements into internal virtual functions for smaller contract size."
    IMPACT = DetectorClassification.OPTIMIZATION
    CONFIDENCE = DetectorClassification.MEDIUM

    WIKI = "https://github.com/demis1997/slither-gas-optimizer-detector/wiki/Solidity-Gas-Optimizations-and-Tricks#use-internal-view-functions-in-modifiers-to-save-bytecode"
    WIKI_TITLE = "Use internal view functions in modifiers to save bytecode"
    WIKI_DESCRIPTION = "Putting the require in an internal function decreases contract size when a modifier is used multiple times. There is no difference in deployment gas cost with private and internal functions."

    def _is_instance(self, ir):  # pylint: disable=no-self-use
        return isinstance(ir, Operation) and ir.operation == "require"

    def _detect(self):
        contract = self.slither.contract
        if len(contract.slithir) > 400:
            return
        require_stmts = set()
        for function in contract.functions:
            if function.visibility != "internal" or not function.is_virtual:
                continue
            has_require = False
            for statement in function.nodes:
                if isinstance(statement, Operation) and statement.operation == "require":
                    has_require = True
                    break
            if has_require:
                require_stmts.add(function)
        if require_stmts:
            return {"issues": {"The following internal virtual functions have require statements outside of them": [f"{f.name} ({f.location})" for f in require_stmts]}}
