from typing import List

from slither.detectors.abstract_detector import (
    AbstractDetector,
    DetectorClassification,
    DETECTOR_INFO,
)
from slither.utils.output import Output
from slither.slithir.operations import Binary, Assignment, Unpack, SolidityCall
from slither.core.variables import Variable
from slither.core.declarations.solidity_variables import SolidityFunction
from slither.core.cfg.node import Node


class ChronicleUncheckedPrice(AbstractDetector):
    """
    Documentation: This detector finds calls to Chronicle oracle where the returned price is not checked
    https://docs.chroniclelabs.org/Resources/FAQ/Oracles#how-do-i-check-if-an-oracle-becomes-inactive-gets-deprecated
    """

    ARGUMENT = "chronicle-unchecked-price"
    HELP = "Detect when Chronicle price is not checked."
    IMPACT = DetectorClassification.MEDIUM
    CONFIDENCE = DetectorClassification.MEDIUM

    WIKI = "https://github.com/crytic/slither/wiki/Detector-Documentation#chronicle-unchecked-price"

    WIKI_TITLE = "Chronicle unchecked price"
    WIKI_DESCRIPTION = "Chronicle oracle is used and the price returned is not checked to be valid. For more information https://docs.chroniclelabs.org/Resources/FAQ/Oracles#how-do-i-check-if-an-oracle-becomes-inactive-gets-deprecated."

    # region wiki_exploit_scenario
    WIKI_EXPLOIT_SCENARIO = """
```solidity
contract C {
    IChronicle chronicle;

    constructor(address a) {
        chronicle = IChronicle(a);
    }

    function bad() public {
        uint256 price = chronicle.read();
    }
```
The `bad` function gets the price from Chronicle by calling the read function however it does not check if the price is valid."""
    # endregion wiki_exploit_scenario

    WIKI_RECOMMENDATION = "Validate that the price returned by the oracle is valid."

    def _var_is_checked(self, nodes: List[Node], var_to_check: Variable) -> bool:
        visited = set()
        checked = False

        while nodes:
            if checked:
                break
            next_node = nodes[0]
            nodes = nodes[1:]

            for node_ir in next_node.all_slithir_operations():
                if isinstance(node_ir, Binary) and var_to_check in node_ir.read:
                    checked = True
                    break
                # This case is for tryRead and tryReadWithAge
                # if the isValid boolean is checked inside a require(isValid)
                if (
                    isinstance(node_ir, SolidityCall)
                    and node_ir.function
                    in (
                        SolidityFunction("require(bool)"),
                        SolidityFunction("require(bool,string)"),
                        SolidityFunction("require(bool,error)"),
                    )
                    and var_to_check in node_ir.read
                ):
                    checked = True
                    break

            if next_node not in visited:
                visited.add(next_node)
                for son in next_node.sons:
                    if son not in visited:
                        nodes.append(son)
        return checked

    # pylint: disable=too-many-nested-blocks,too-many-branches
    def _detect(self) -> List[Output]:
        results: List[Output] = []

        for contract in self.compilation_unit.contracts_derived:
            for target_contract, ir in sorted(
                contract.all_high_level_calls,
                key=lambda x: (x[1].node.node_id, x[1].node.function.full_name),
            ):
                if target_contract.name in ("IScribe", "IChronicle") and ir.function_name in (
                    "read",
                    "tryRead",
                    "readWithAge",
                    "tryReadWithAge",
                    "latestAnswer",
                    "latestRoundData",
                ):
                    found = False
                    if ir.function_name in ("read", "latestAnswer"):
                        # We need to iterate the IRs as we are not always sure that the following IR is the assignment
                        # for example in case of type conversion it isn't
                        for node_ir in ir.node.irs:
                            if isinstance(node_ir, Assignment):
                                possible_unchecked_variable_ir = node_ir.lvalue
                                found = True
                                break
                    elif ir.function_name in ("readWithAge", "tryRead", "tryReadWithAge"):
                        # We are interested in the first item of the tuple
                        # readWithAge : value
                        # tryRead/tryReadWithAge : isValid
                        for node_ir in ir.node.irs:
                            if isinstance(node_ir, Unpack) and node_ir.index == 0:
                                possible_unchecked_variable_ir = node_ir.lvalue
                                found = True
                                break
                    elif ir.function_name == "latestRoundData":
                        found = False
                        for node_ir in ir.node.irs:
                            if isinstance(node_ir, Unpack) and node_ir.index == 1:
                                possible_unchecked_variable_ir = node_ir.lvalue
                                found = True
                                break

                    # If we did not find the variable assignment we know it's not checked
                    checked = (
                        self._var_is_checked(ir.node.sons, possible_unchecked_variable_ir)
                        if found
                        else False
                    )

                    if not checked:
                        info: DETECTOR_INFO = [
                            "Chronicle price is not checked to be valid in ",
                            ir.node.function,
                            "\n\t- ",
                            ir.node,
                            "\n",
                        ]
                        res = self.generate_result(info)
                        results.append(res)

        return results
