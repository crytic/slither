"""
    Module detecting state uninitialized variables
    Recursively check the called functions

    The heuristic checks:
    - state variables including mappings/refs
    - LibraryCalls, InternalCalls, InternalDynamicCalls with storage variables

    Only analyze "leaf" contracts (contracts that are not inherited by another contract)
"""

from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification
from slither.slithir.operations import InternalCall, LibraryCall
from slither.slithir.variables import ReferenceVariable


class UninitializedStateVarsDetection(AbstractDetector):
    """
    Constant function detector
    """

    ARGUMENT = "uninitialized-state"
    HELP = "Uninitialized state variables"
    IMPACT = DetectorClassification.HIGH
    CONFIDENCE = DetectorClassification.HIGH

    WIKI = "https://github.com/crytic/slither/wiki/Detector-Documentation#uninitialized-state-variables"

    WIKI_TITLE = "Uninitialized state variables"
    WIKI_DESCRIPTION = "Uninitialized state variables."
    WIKI_EXPLOIT_SCENARIO = """
```solidity
contract Uninitialized{
    address destination;

    function transfer() payable public{
        destination.transfer(msg.value);
    }
}
```
Bob calls `transfer`. As a result, the Ether are sent to the address `0x0` and are lost.
"""
    WIKI_RECOMMENDATION = """
Initialize all the variables. If a variable is meant to be initialized to zero, explicitly set it to zero to improve code readability.
"""

    @staticmethod
    def _written_variables(contract):
        ret = []
        # pylint: disable=too-many-nested-blocks
        for f in contract.all_functions_called + contract.modifiers:
            for n in f.nodes:
                ret += n.state_variables_written
                for ir in n.irs:
                    if isinstance(ir, (LibraryCall, InternalCall)):
                        idx = 0
                        if ir.function:
                            for param in ir.function.parameters:
                                if param.location == "storage":
                                    # If its a storage variable, add either the variable
                                    # Or the variable it points to if its a reference
                                    if isinstance(ir.arguments[idx], ReferenceVariable):
                                        ret.append(ir.arguments[idx].points_to_origin)
                                    else:
                                        ret.append(ir.arguments[idx])
                                idx = idx + 1

        return ret

    def _variable_written_in_proxy(self):
        # Hack to memoize without having it define in the init
        if hasattr(self, "__variables_written_in_proxy"):
            # pylint: disable=access-member-before-definition
            return self.__variables_written_in_proxy

        variables_written_in_proxy = []
        for c in self.compilation_unit.contracts:
            if c.is_upgradeable_proxy:
                variables_written_in_proxy += self._written_variables(c)

        # pylint: disable=attribute-defined-outside-init
        self.__variables_written_in_proxy = list({v.name for v in variables_written_in_proxy})
        return self.__variables_written_in_proxy

    def _written_variables_in_proxy(self, contract):
        variables = []
        if contract.is_upgradeable:
            variables_name_written_in_proxy = self._variable_written_in_proxy()
            if variables_name_written_in_proxy:
                variables_in_contract = [
                    contract.get_state_variable_from_name(v)
                    for v in variables_name_written_in_proxy
                ]
                variables_in_contract = [v for v in variables_in_contract if v]
                variables += variables_in_contract
        return list(set(variables))

    @staticmethod
    def _read_variables(contract):
        ret = []
        for f in contract.all_functions_called + contract.modifiers:
            ret += f.state_variables_read
        return ret

    def _detect_uninitialized(self, contract):
        written_variables = self._written_variables(contract)
        written_variables += self._written_variables_in_proxy(contract)
        read_variables = self._read_variables(contract)
        return [
            (variable, contract.get_functions_reading_from_variable(variable))
            for variable in contract.state_variables
            if variable not in written_variables
            and not variable.expression
            and variable in read_variables
        ]

    def _detect(self):
        """Detect uninitialized state variables

        Recursively visit the calls
        Returns:
            dict: [contract name] = set(state variable uninitialized)
        """
        results = []
        for c in self.compilation_unit.contracts_derived:
            ret = self._detect_uninitialized(c)
            for variable, functions in ret:

                info = [variable, " is never initialized. It is used in:\n"]

                for f in functions:
                    info += ["\t- ", f, "\n"]

                json = self.generate_result(info)
                results.append(json)

        return results
