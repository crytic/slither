from typing import List

from slither.core.declarations import SolidityFunction, Function
from slither.core.declarations.contract import Contract
from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification
from slither.slithir.operations import LowLevelCall, SolidityCall


def _can_be_destroyed(contract: Contract) -> List[Function]:
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

def _has_initializing_protection(functions: List[Function]) -> bool:
    # Detects "initializer" constructor modifiers and "_disableInitializers()" constructor internal calls
    # https://docs.openzeppelin.com/upgrades-plugins/1.x/writing-upgradeable#initializing_the_implementation_contract

    for f in functions:
        for m in f.modifiers:
            if m.name == "initializer":
                return True
        for ifc in f.all_internal_calls() :
            if ifc.name == "_disableInitializers":
                return True

    # to avoid future FPs in different modifier + function naming implementations, we can also implement a broader check for state var "_initialized" being written to in the constructor
    #   though this is still subject to naming false positives... 
    return False


def _whitelisted_modifiers(f: Function) -> bool:
    # The onlyProxy modifier prevents calling the implementation contract (must be delegatecall)
    #  https://github.com/OpenZeppelin/openzeppelin-contracts-upgradeable/blob/3dec82093ea4a490d63aab3e925fed4f692909e8/contracts/proxy/utils/UUPSUpgradeable.sol#L38-L42
    return "onlyProxy" not in [modifier.name for modifier in f.modifiers]


def _initialize_functions(contract: Contract) -> List[Function]:
    return list(
        filter(_whitelisted_modifiers, [f for f in contract.functions if f.name == "initialize"])
    )


class UnprotectedUpgradeable(AbstractDetector):

    ARGUMENT = "unprotected-upgrade"
    HELP = "Unprotected upgradeable contract"
    IMPACT = DetectorClassification.HIGH
    CONFIDENCE = DetectorClassification.HIGH

    WIKI = "https://github.com/crytic/slither/wiki/Detector-Documentation#unprotected-upgradeable-contract"

    WIKI_TITLE = "Unprotected upgradeable contract"
    WIKI_DESCRIPTION = """Detects logic contract that can be destructed."""

    # region wiki_exploit_scenario
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
    # endregion wiki_exploit_scenario

    WIKI_RECOMMENDATION = (
        """Add a constructor to ensure `initialize` cannot be called on the logic contract."""
    )

    def _detect(self):
        results = []

        for contract in self.compilation_unit.contracts_derived:
            if contract.is_upgradeable:
                if not _has_initializing_protection(contract.constructors):
                    functions_that_can_destroy = _can_be_destroyed(contract)
                    if functions_that_can_destroy:
                        initialize_functions = _initialize_functions(contract)

                        vars_init_ = [
                            init.all_state_variables_written() for init in initialize_functions
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
                                    " is an upgradeable contract that does not protect its initialize functions: ",
                                ]
                                + initialize_functions
                                + [
                                    ". Anyone can delete the contract with: ",
                                ]
                                + functions_that_can_destroy
                            )

                            res = self.generate_result(info)
                            results.append(res)

        return results
