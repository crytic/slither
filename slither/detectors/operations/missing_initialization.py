"""
Module detecting missing initialization used to check conditions.

"""

from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification
from slither.core.declarations.solidity_variables import SolidityFunction


class MissingInitialization(AbstractDetector):
    """
    Detect missing-initialization
    """

    ARGUMENT = (
        "missing-initialization"  # slither will launch the detector with slither.py --mydetector
    )
    HELP = "Initialize function misses initialization"
    IMPACT = DetectorClassification.HIGH
    CONFIDENCE = DetectorClassification.HIGH

    WIKI = (
        "https://github.com/trailofbits/slither/wiki/Detector-Documentation#missing-initialization"
    )
    WIKI_TITLE = "MISSING_INITIALIZATION"
    WIKI_DESCRIPTION = "MISSING_INITIALIZATION"
    WIKI_EXPLOIT_SCENARIO = """
```solidity
contract A {
    uint public state_variable = 0;
    bool public initialized = false;

    modifier not_initialized(){
        require(initialized == false);
        _;
    }

    function initialize(uint _state_variable) public not_initialized {
        state_variable = _state_variable;
    }
}
```
Bob calls `initialize`. However, Alice can also call `initialize`.
"""
    WIKI_RECOMMENDATION = "Check state variable should be initialized in initialize function"

    def detect_initilize(self, func):
        if "init" in func.name.lower():
            return True
        return False

    def explore(self, _func, _set, _visited):
        if _func in _visited:
            return
        _visited.append(_func)

        _set += _func.state_variables_written

        for func in _func.internal_calls + _func.modifiers:
            if isinstance(func, SolidityFunction):
                continue
            self.explore(func, _set, _visited)

    def check_state_variables_in_conditions_are_initialzed(self, func):
        should_be_initialized = []
        initialized_in_init = []

        self.explore(func, initialized_in_init, [])
        should_be_initialized = func.all_conditional_state_variables_read()

        if set(should_be_initialized) == (set(should_be_initialized) & set(initialized_in_init)):
            return True
        return False

    def _detect(self):
        results = []

        for contract in self.compilation_unit.contracts:
            for f in contract.functions:
                # Check if a function has 'init' in its name
                if self.detect_initilize(f):
                    # Check if condition variable is initialized
                    if not self.check_state_variables_in_conditions_are_initialzed(f):
                        info = [
                            "Condition variable is not initialized in ",
                            f,
                            "\n",
                        ]
                        res = self.generate_result(info)
                        results.append(res)
        return results
