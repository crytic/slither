from typing import List

from slither.core.declarations import SolidityFunction, Function
from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification
from slither.slithir.operations import LowLevelCall, SolidityCall


def _can_be_destroyed(contract) -> List[Function]:
    targets = []
    for f in contract.functions_entry_points:
        for ir in f.all_slithir_operations():
            if (
                isinstance(ir, LowLevelCall) and ir.function_name in ["delegatecall", "codecall"]
            ) or (
                isinstance(ir, SolidityCall)
                and ir.function
                in [SolidityFunction("suicide(address)"), SolidityFunction("selfdestruct(address)")]
            ):
                targets.append(f)
                break
    return targets


class UnprotectedUpgradeable(AbstractDetector):
    """
    """

    ARGUMENT = "unprotected-upgrade"
    HELP = "Unprotected upgradeable contract"
    IMPACT = DetectorClassification.HIGH
    CONFIDENCE = DetectorClassification.HIGH

    WIKI = (
        "https://github.com/crytic/slither/wiki/Detector-Documentation#unprotected-upgradeable-contract"
    )

    WIKI_TITLE = "Unprotected upgradeable contract"
    WIKI_DESCRIPTION = """Detects logic contract that can be destructed."""
    WIKI_EXPLOIT_SCENARIO = """
    ```solidity
    contract Buggy is Initializable{
        address payable owner;
    
        function initialize() external initializer{
            require(owner == address(0));
            owner = msg.sender;
        }
        function kill() external{
            require(msg.sender == owner);
            selfdestruct(owner);
        }
    }
    ```
    Buggy is an upgradeable contract. Anyone can call initialize on the logic contract, and destruct the contract."""

    WIKI_RECOMMENDATION = """Add a constructor to ensure `initialize` cannot be called on the logic contract."""

    def _detect(self):
        results = []

        for contract in self.slither.contracts_derived:
            if contract.is_upgradeable:
                functions_that_can_destroy = _can_be_destroyed(contract)
                if functions_that_can_destroy:
                    initiliaze_functions = [f for f in contract.functions if f.name == "initialize"]
                    vars_init_ = [
                        init.all_state_variables_written() for init in initiliaze_functions
                    ]
                    vars_init = [item for sublist in vars_init_ for item in sublist]

                    vars_init_in_constructors_ = [
                        f.all_state_variables_written() for f in contract.constructors
                    ]
                    vars_init_in_constructors = [
                        item for sublist in vars_init_in_constructors_ for item in sublist
                    ]
                    if vars_init and (set(vars_init) - set(vars_init_in_constructors)):
                        info = (
                            [
                                contract,
                                " is an upgradeable contract that does not protect its initiliaze functions: ",
                            ]
                            + initiliaze_functions
                            + [". Anyone can delete the contract with: ",]
                            + functions_that_can_destroy
                        )

                        res = self.generate_result(info)
                        results.append(res)

        return results
