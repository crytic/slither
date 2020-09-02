"""
Module detecting constant functions
Recursively check the called functions
"""
from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification
from slither.formatters.attributes.const_functions import custom_format


class ConstantFunctionsState(AbstractDetector):
    """
    Constant function detector
    """

    ARGUMENT = "constant-function-state"  # run the detector with slither.py --ARGUMENT
    HELP = "Constant functions changing the state"  # help information
    IMPACT = DetectorClassification.MEDIUM
    CONFIDENCE = DetectorClassification.MEDIUM

    WIKI = "https://github.com/crytic/slither/wiki/Detector-Documentation#constant-functions-changing-the-state"

    WIKI_TITLE = "Constant functions changing the state"
    WIKI_DESCRIPTION = """
Functions declared as `constant`/`pure`/`view` change the state.

`constant`/`pure`/`view` was not enforced prior to Solidity 0.5.
Starting from Solidity 0.5, a call to a `constant`/`pure`/`view` function uses the `STATICCALL` opcode, which reverts in case of state modification.

As a result, a call to an [incorrectly labeled function may trap a contract compiled with Solidity 0.5](https://solidity.readthedocs.io/en/develop/050-breaking-changes.html#interoperability-with-older-contracts)."""

    WIKI_EXPLOIT_SCENARIO = """
```solidity
contract Constant{
    uint counter;
    function get() public view returns(uint){
       counter = counter +1;
       return counter
    }
}
```
`Constant` was deployed with Solidity 0.4.25. Bob writes a smart contract that interacts with `Constant` in Solidity 0.5.0. 
All the calls to `get` revert, breaking Bob's smart contract execution."""

    WIKI_RECOMMENDATION = "Ensure that attributes of contracts compiled prior to Solidity 0.5.0 are correct."

    def _detect(self):
        """ Detect the constant function changing the state

        Recursively visit the calls
        Returns:
            list: {'vuln', 'filename,'contract','func','#varsWritten'}
        """
        results = []
        if self.slither.solc_version and self.slither.solc_version >= "0.5.0":
            return results
        for c in self.contracts:
            for f in c.functions:
                if f.contract_declarer != c:
                    continue
                if f.view or f.pure:
                    variables_written = f.all_state_variables_written()
                    if variables_written:
                        attr = "view" if f.view else "pure"

                        info = [
                            f,
                            f" is declared {attr} but changes state variables:\n",
                        ]

                        for variable_written in variables_written:
                            info += ["\t- ", variable_written, "\n"]

                        res = self.generate_result(info, {"contains_assembly": False})

                        results.append(res)

        return results

    @staticmethod
    def _format(slither, result):
        custom_format(slither, result)
