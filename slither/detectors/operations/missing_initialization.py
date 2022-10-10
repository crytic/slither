"""
Module detecting missing initialization used to check conditions.

"""

from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification


class MissingInitialization(AbstractDetector):
    """
    Detect missing-initialization
    """

    ARGUMENT = "missing-initialization"  # slither will launch the detector with slither.py --mydetector
    HELP = "Initialize function misses initialization"
    IMPACT = DetectorClassification.HIGH
    CONFIDENCE = DetectorClassification.HIGH

    WIKI = "https://github.com/trailofbits/slither/wiki/Detector-Documentation#missing-initialization"
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
    WIKI_RECOMMENDATION = (
        "Check state variable should be initialized in initialize function"
    )

    def detect_initilize(self, func):
        if "init" in func.name:
            return True
        return False

    def detect_validation(self, func):
        # modifier
        if func.modifiers_statements:
            return True

        for node in func.nodes:
            # require or assert or if
            if node.contains_if() or node.contains_require_or_assert():
                return True
        return False

    def check_state_variables_in_conditions_are_initialzed(self, func):
        should_be_initialized = []
        initialized_in_init = []

        for svw in func.state_variables_written:
            initialized_in_init += [svw.name]

        for name in func.all_conditional_state_variables_read():
            should_be_initialized += [name]

        if set(should_be_initialized) in set(initialized_in_init):
            return True
        return False

    def _detect(self):
        results = []

        for contract in self.compilation_unit.contracts:
            for f in contract.functions:
                # Check if a function has 'init' in its name
                if self.detect_initilize(f):
                    # Chceck if it has validation
                    if not self.detect_validation(f):
                        # Info to be printed
                        info = [
                            "Initialize function does not have validation found in ",
                            f,
                            "\n",
                        ]
                        # Add the result in result
                        res = self.generate_result(info)
                        results.append(res)
                    # Check if condition variable is initialized
                    if not self.check_state_variables_in_conditions_are_initialzed(f):
                        # Info to be printed
                        info = [
                            "Variable is Not initialized in initialize() found in ",
                            f,
                            "\n",
                        ]
                        # Add the result in result
                        res = self.generate_result(info)
                        results.append(res)
        return results
