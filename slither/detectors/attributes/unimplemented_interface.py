"""
Module detecting unimplemented interfaces

Collect all the interfaces
Check for contracts which implement all interface functions but do not explicitly derive from those interfaces.
"""
from typing import List
from slither.detectors.abstract_detector import (
    AbstractDetector,
    DetectorClassification,
    DETECTOR_INFO,
)
from slither.core.declarations.contract import Contract
from slither.utils.output import Output


class MissingInheritance(AbstractDetector):
    """
    Unimplemented interface detector
    """

    ARGUMENT = "missing-inheritance"
    HELP = "Missing inheritance"
    IMPACT = DetectorClassification.INFORMATIONAL
    CONFIDENCE = DetectorClassification.HIGH

    WIKI = "https://github.com/crytic/slither/wiki/Detector-Documentation#missing-inheritance"
    WIKI_TITLE = "Missing inheritance"
    WIKI_DESCRIPTION = "Detect missing inheritance."

    # region wiki_exploit_scenario
    WIKI_EXPLOIT_SCENARIO = """
```solidity
interface ISomething {
    function f1() external returns(uint);
}

contract Something {
    function f1() external returns(uint){
        return 42;
    }
}
```
`Something` should inherit from `ISomething`. 
"""
    # endregion wiki_exploit_scenario

    WIKI_RECOMMENDATION = "Inherit from the missing interface or contract."

    @staticmethod
    def detect_unimplemented_interface(
        contract: Contract, interfaces: List[Contract]
    ) -> List[Contract]:
        """
        Detects if contract intends to implement one of the interfaces but does not explicitly do so by deriving from it
        :param contract: The contract to check
        :param interfaces: List of all the interfaces
        :return: Interfaces likely intended to implement by the contract
        """

        intended_interfaces: List[Contract] = []
        sigs_contract = {f.full_name for f in contract.functions_entry_points}

        if not sigs_contract:
            return intended_interfaces

        for interface in interfaces:
            # If contract already inherits from interface, skip that interface
            if interface in contract.inheritance:
                continue

            sigs_interface = {f.full_name for f in interface.functions_entry_points}

            # Contract should implement all the functions of the intended interface
            if not sigs_interface.issubset(sigs_contract):
                continue

            # A parent contract inherited should not implement a superset of intended interface
            # This is because in the following:
            # interface ERC20_interface:
            #    - balanceOf(uint) -> uint
            #    - transfer(address, address) -> bool
            # contract ForeignToken:
            #    - balanceOf(uint) -> uint
            # contract MyERC20Implementation is ERC20_interface
            #
            # We do not want MyERC20Implementation to be declared as missing ForeignToken interface
            intended_interface_is_subset_parent = False
            for parent in contract.inheritance:
                sigs_parent = {f.full_name for f in parent.functions_entry_points}
                if sigs_interface.issubset(sigs_parent):
                    intended_interface_is_subset_parent = True
                    break

            if not intended_interface_is_subset_parent:
                # Should not be a subset of an earlier determined intended_interface or derive from it
                intended_interface_is_subset_intended = False
                for intended_interface in list(intended_interfaces):
                    sigs_intended_interface = {
                        f.full_name for f in intended_interface.functions_entry_points
                    }
                    if (
                        sigs_interface.issubset(sigs_intended_interface)
                        or interface in intended_interface.inheritance
                    ):
                        intended_interface_is_subset_intended = True
                        break

                    # If superset of an earlier determined intended_interface or derives from it,
                    # remove the intended_interface
                    if (
                        sigs_intended_interface.issubset(sigs_interface)
                        or intended_interface in interface.inheritance
                    ):
                        intended_interfaces.remove(intended_interface)

                if not intended_interface_is_subset_intended:
                    intended_interfaces.append(interface)

        return intended_interfaces

    def _detect(self) -> List[Output]:
        """Detect unimplemented interfaces
        Returns:
            list: {'contract'}
        """

        # Collect all the interfaces
        # Here interface can be "interface" from solidity, or contracts with only functions declaration
        # Skip interfaces without functions
        interfaces = [
            contract
            for contract in self.compilation_unit.contracts
            if contract.is_signature_only()
            and any(not f.is_constructor_variables for f in contract.functions)
        ]

        # Check derived contracts for missing interface implementations
        results = []
        for contract in self.compilation_unit.contracts_derived:
            # Skip interfaces
            if contract in interfaces:
                continue
            intended_interfaces = self.detect_unimplemented_interface(contract, interfaces)
            for interface in intended_interfaces:
                info: DETECTOR_INFO = [contract, " should inherit from ", interface, "\n"]
                res = self.generate_result(info)
                results.append(res)
        return results
