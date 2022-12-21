"""
Module detecting dangerous external call.

"""

from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification
from slither.slithir.operations import Binary, BinaryType
from slither.slithir.operations.solidity_call import SolidityCall
from slither.slithir.operations.high_level_call import HighLevelCall
from slither.slithir.operations.library_call import LibraryCall
from slither.slithir.operations.internal_call import InternalCall
from slither.core.declarations.function import FunctionType
from slither.analyses.data_dependency.data_dependency import get_all_dependencies
from slither.core.declarations.function import FunctionType
from slither.core.declarations.solidity_variables import SolidityVariableComposed
from slither.slithir.operations.index import Index
from slither.core.declarations.modifier import Modifier
import re


class DangerousExternalCall(AbstractDetector):
    """
    Detect dangerous-external-call
    """

    ARGUMENT = "dangerous-external-call"
    HELP = "External call by using unverified address"
    IMPACT = DetectorClassification.HIGH
    CONFIDENCE = DetectorClassification.MEDIUM

    WIKI = "https://github.com/crytic/slither/wiki/Detector-Documentation#dangerous-external-call"
    WIKI_TITLE = "DANGEROUS_EXTERNAL_CALL"
    WIKI_DESCRIPTION = "DANGEROUS_EXTERNAL_CALL"
    WIKI_EXPLOIT_SCENARIO = """
```solidity
interface IERC20 {
    function safeTransferFrom (address, address, uint) external;
}
contract A {
    function depositFor(address token, uint _amount,address user ) public {
        IERC20(token).safeTransferFrom(msg.sender, address(this), _amount); //vulnerable point
    }
}
```
https://ftmscan.com/address/0x660184ce8af80e0b1e5a1172a16168b15f4136bf#code#L1115
https://rekt.news/grim-finance-rekt/

Attacker can input fake token address because there is no verification of token address.
"""
    WIKI_RECOMMENDATION = "Add verification of address to function calling external call"

    # heuristic 1: Before calling, external call's address might be verfied.
    def explore(self, _contract, _func, _visited: dict, _binary_operands: set):

        if _func in _visited:
            return _visited[_func]

        _visited[_func] = False

        dependency = get_all_dependencies(_contract)
        # _func is internal func or modifier?
        # modifier does not external call.
        if isinstance(_func, Modifier):
            internal_calls = []
            for node in _func.nodes:
                for ir in node.irs:
                    # not modifier
                    if isinstance(ir, InternalCall) and not isinstance(ir.function, Modifier):
                        internal_calls.append(ir.function)

                    # collect binary operand
                    if isinstance(ir, Binary) and ir._type in [
                        BinaryType.EQUAL,
                        BinaryType.NOT_EQUAL,
                    ]:
                        for op in ir.read:
                            _binary_operands.add(op)

                    # access-control
                    # require(isExcluded[msg.sender])
                    # require(msg.sender == owner)
                    if isinstance(ir, SolidityCall) and "require" in ir.function.full_name:
                        for op in ir.arguments:
                            if (
                                op in dependency
                                and SolidityVariableComposed("msg.sender") in dependency[op]
                            ):
                                self.access_control = True
                                # print(node.expression)

            for mod in _func.modifiers:
                _visited[_func] |= self.explore(_contract, mod, _visited, _binary_operands)

            for func in internal_calls:
                _visited[_func] |= self.explore(_contract, func, _visited, _binary_operands)

        else:

            for mod in _func.modifiers:
                _visited[_func] |= self.explore(_contract, mod, _visited, _binary_operands)

            for node in _func.nodes:
                for ir in node.irs:
                    # not modifier
                    if isinstance(ir, InternalCall) and not isinstance(ir.function, Modifier):
                        _visited[_func] |= self.explore(
                            _contract, ir.function, _visited, _binary_operands
                        )

                    # collect binary operand
                    if isinstance(ir, Binary) and ir._type in [
                        BinaryType.EQUAL,
                        BinaryType.NOT_EQUAL,
                    ]:
                        for op in ir.read:
                            _binary_operands.add(op)

                    # access-control
                    # require(isExcluded[msg.sender])
                    # require(msg.sender == owner)
                    if isinstance(ir, SolidityCall) and "require" in ir.function.full_name:
                        for op in ir.arguments:
                            if (
                                op in dependency
                                and SolidityVariableComposed("msg.sender") in dependency[op]
                            ):
                                self.access_control = True
                                # print(node.expression)

                    # external call
                    if isinstance(ir, HighLevelCall):

                        # SafeErc
                        if (
                            isinstance(ir, LibraryCall)
                            and ir._destination.name.lower() == "safemath"
                        ):
                            continue

                        self.answer = False

                        # dest is state variable?
                        dest = re.findall(r"\([a-zA-Z0-9_]+\)", str(ir.expression))
                        dest2 = str(ir.expression).split(".")

                        if (
                            len(dest) > 0
                            and any(vari.name == dest[0][1:-1] for vari in _contract.variables)
                        ) or (
                            (len(dest2) > 0)
                            and any(vari.name == dest2[0] for vari in _contract.variables)
                        ):
                            continue

                        data = ir.destination
                        for op in _binary_operands:
                            if op in dependency and data in dependency[op]:
                                self.answer = True

                            if data in dependency:
                                if any(op == _data for _data in dependency[data]):
                                    self.answer = True

                                if op in dependency and data in dependency:
                                    for _data in dependency[data]:
                                        if _data in dependency[op]:
                                            self.answer = True

                        if self.answer == False and self.access_control == False:
                            info = [
                                "Dangerous external call in ",
                                _func,
                                "\n",
                            ]
                            res = self.generate_result(info)
                            self.results.append(res)
        return _visited[_func]

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
        self.results = []

        for contract in self.compilation_unit.contracts:
            for function in contract.functions:

                if "init" in function.name.lower() and any(
                    mod.name
                    in ["initializer", "reinitializer", "onlyInitializing", "_disableInitializers"]
                    for mod in function.modifiers
                ):
                    continue

                if (
                    function._pure == True
                    or function._view == True
                    or function._visibility in ["internal", "private"]
                    or function._function_type == FunctionType.CONSTRUCTOR
                ):
                    continue

                self.access_control = False
                self.explore(contract, function, {}, set())

        return self.results
