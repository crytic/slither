"""
Module detecting improper access control.

"""

from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification
from slither.slithir.operations.internal_call import InternalCall
from slither.slithir.operations.solidity_call import SolidityCall
from slither.core.declarations.function import FunctionType
from slither.core.declarations.solidity_variables import SolidityFunction
from slither.slithir.operations.index import Index
from slither.core.declarations.solidity_variables import SolidityVariableComposed
from slither.slithir.operations.internal_call import InternalCall
from slither.slithir.operations.condition import Condition
from slither.slithir.operations.binary import Binary
from slither.analyses.data_dependency.data_dependency import get_all_dependencies
from slither.core.declarations.function import FunctionType
from slither.core.declarations.solidity_variables import SolidityVariableComposed
from slither.slithir.operations.condition import Condition


class AccessControl(AbstractDetector):
    """
    Detect when writting state variable, but there is no access control
    """

    ARGUMENT = "access-control"  # slither will launch the detector with slither.py --mydetector
    HELP = "Function misses access control"
    IMPACT = DetectorClassification.HIGH
    CONFIDENCE = DetectorClassification.MEDIUM

    WIKI = (
        "https://github.com/trailofbits/slither/wiki/Detector-Documentation#improper-access-control"
    )
    WIKI_TITLE = "ACCESS_CONTROL"
    WIKI_DESCRIPTION = "ACCESS_CONTROL"
    WIKI_EXPLOIT_SCENARIO = """
```solidity
contract A {
    address token;

    function setToken(address _token) public {
        token = _token;
    }
}
```
Bob can calls `setToken` to change token address.
"""
    WIKI_RECOMMENDATION = "Check state variable should be protected"

    def all_state_variables_written(self, _function, _visited, _result):
        if _function in _visited:
            return
        _visited.append(_function)

        if isinstance(_function, SolidityFunction):
            return

        _result += _function.state_variables_written

        for function in _function.modifiers + _function.internal_calls:
            if function in _visited:
                continue

            self.all_state_variables_written(function, _visited, _result)

    # Like DFS
    def is_protected(self, _contract, _function, visited):

        if _function in visited:
            return visited[_function]

        visited[_function] = False
        flag = _function._is_protected
        dependency = get_all_dependencies(_contract)

        for node in _function.nodes:
            for ir in node.irs:

                # require(isExcluded[msg.sender])
                if isinstance(ir, SolidityCall) and "require" in ir.function.full_name:
                    for op in ir.arguments:
                        if (
                            op in dependency
                            and SolidityVariableComposed("msg.sender") in dependency[op]
                        ):
                            flag = True

                # if(isExcluded[msg.sender])
                if isinstance(ir, Condition):
                    for op in ir.read:
                        if (
                            op in dependency
                            and SolidityVariableComposed("msg.sender") in dependency[op]
                        ):
                            flag = True

                # require(msg.sender == owner)
                if isinstance(ir, Binary):
                    for op in ir.read:
                        if (
                            op in dependency
                            and SolidityVariableComposed("msg.sender") in dependency[op]
                        ):
                            flag = True

                # isOwner(msg.sender)
                if isinstance(ir, InternalCall):  # internal call + modifier
                    for op in ir.arguments:
                        if (
                            op in dependency
                            and SolidityVariableComposed("msg.sender") in dependency[op]
                        ):
                            flag = True

        for nxt in _function.modifiers + _function._internal_calls:
            if isinstance(nxt, SolidityFunction):
                continue
            flag |= self.is_protected(_contract, nxt, visited)

        visited[_function] = flag
        return flag

    def _detect(self):

        KEY_NON_SSA = "DATA_DEPENDENCY"

        for contract in self.compilation_unit.contracts:
            t = get_all_dependencies(contract)

            for function in contract.functions + contract.modifiers:
                for node in function.nodes:
                    for ir in node.irs:

                        # At a = b[index], add 'index' to 'data dependency of a'
                        if isinstance(ir, Index):

                            # data_dependency[index] = index
                            # data_dependency[a] += index
                            if ir.variable_right not in t:
                                contract.context[KEY_NON_SSA][ir.lvalue].add(ir.variable_right)
                                contract.context[KEY_NON_SSA][ir.variable_right] = set(
                                    [ir.variable_right]
                                )

                            # data_dependency[a] += data_dependency[index]
                            else:
                                for i in t[ir.variable_right]:
                                    contract.context[KEY_NON_SSA][ir.lvalue].add(i)

                            # if a in data_dependency[?] -> data_dependency[?] += data_dependency[index]
                            for key, value in t.items():
                                if ir.lvalue in value:
                                    for i in t[ir.variable_right]:
                                        contract.context[KEY_NON_SSA][key].add(i)

        results = []

        # well known function might be access control
        well_known = ["init", "set", "mint", "burn", "owner", "gov"]
        # write something on storage
        self.init = ["init", "set"]
        # written in init
        self.init_state_variable = []

        for contract in self.compilation_unit.contracts:
            for function in contract.functions:
                if function._function_type == FunctionType.CONSTRUCTOR or any(
                    i in function.name.lower() for i in self.init
                ):
                    self.all_state_variables_written(function, [], self.init_state_variable)

        for contract in self.compilation_unit.contracts:
            for function in contract.functions:
                if (
                    function._pure == True
                    or function._view == True
                    or function._visibility in ["internal", "private"]
                ):
                    continue

            if contract._is_interface == True:
                continue

            for function in contract.functions:

                if len(function.nodes) <= 1:
                    continue

                if "init" in function.name.lower() and any(
                    mod.name
                    in ["initializer", "reinitializer", "onlyInitializing", "_disableInitializers"]
                    for mod in function.modifiers
                ):
                    continue

                if function.payable:
                    continue

                if (
                    function._pure == True
                    or function._view == True
                    or function._visibility in ["internal", "private"]
                    or function._function_type == FunctionType.CONSTRUCTOR
                ):
                    continue

                # to decrease false positive
                if function.name.lower() in [
                    "transfer",
                    "transferfrom",
                    "approve",
                    "setapprovalforall",
                    "approvemax",
                ]:
                    continue

                if self.is_protected(contract, function, {}):
                    continue

                if any(i in function.name.lower() for i in well_known):
                    info = [
                        "Improper access control found in ",
                        function,
                        "\n",
                    ]
                    res = self.generate_result(info)
                    results.append(res)
                    continue

                self.written_in_function = []
                self.all_state_variables_written(function, [], self.written_in_function)

                intersection = list(set(self.init_state_variable) & set(self.written_in_function))

                if len(intersection) > 0:
                    info = [
                        "Improper access control found in ",
                        function,
                        "\n",
                    ]
                    res = self.generate_result(info)
                    results.append(res)

        return results
