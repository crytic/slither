"""
Module detecting arbitary-calldata.

"""

from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification
from slither.slithir.operations import Binary, BinaryType
from slither.slithir.operations.solidity_call import SolidityCall
from slither.slithir.variables.constant import Constant
from slither.core.declarations.modifier import Modifier
from slither.core.declarations import SolidityFunction
from slither.slithir.operations.low_level_call import LowLevelCall
from slither.slithir.operations.internal_call import InternalCall
from slither.slithir.operations import Index, SolidityCall
from slither.analyses.data_dependency.data_dependency import get_all_dependencies
from slither.slithir.variables.constant import Constant
from slither.core.declarations.solidity_variables import SolidityVariableComposed


class ArbitaryCalldata(AbstractDetector):
    """
    Detect arbitary-calldata
    """

    ARGUMENT = "arbitary-calldata"
    HELP = "When calling call() or delegatecall(), calldata is not verified"
    IMPACT = DetectorClassification.HIGH
    CONFIDENCE = DetectorClassification.MEDIUM

    WIKI = "https://github.com/crytic/slither/wiki/Detector-Documentation#arbitary-calldata"
    WIKI_TITLE = "ARBITARY_CALLDATA"
    WIKI_DESCRIPTION = "ARBITARY_CALLDATA"
    WIKI_EXPLOIT_SCENARIO = """
```solidity
contract A {
    function permit(address token, bytes calldata data) public {
        (bool success, ) = token.call(data);
        require(success, "failure of call()");
    }
}
```
Attacker can call any function.
"""
    WIKI_RECOMMENDATION = "Check calldata is verified"

    # heuristic 1: Before calling, data of call(data) might be verfied.
    def explore(self, _contract, _func, _visited: dict, _binary_operands: set):
        if _func in _visited:
            return _visited[_func]

        _visited[_func] = False

        dependency = get_all_dependencies(_contract)
        # _func is internal func or modifier?
        # modifier does not call() or delegatecall()
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

                    # require(isExcluded[msg.sender])
                    # require(msg.sender == owner)
                    if isinstance(ir, SolidityCall) and "require" in ir.function.full_name:
                        for op in ir.arguments:
                            if (
                                op in dependency
                                and SolidityVariableComposed("msg.sender") in dependency[op]
                            ):
                                self.access_control = True

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

                    # require(isExcluded[msg.sender])
                    # require(msg.sender == owner)
                    if isinstance(ir, SolidityCall) and "require" in ir.function.full_name:
                        for op in ir.arguments:
                            if (
                                op in dependency
                                and SolidityVariableComposed("msg.sender") in dependency[op]
                            ):
                                self.access_control = True

                    # call() or delegatecall()
                    if isinstance(ir, LowLevelCall) and ir._function_name in [
                        "call",
                        "delegatecall",
                    ]:
                        # call{value: 1 ether}();
                        if isinstance(ir._arguments[0], Constant):
                            continue

                        self.answer = False

                        data = ir._arguments[0]
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
                            from slither.utils.source_mapping import get_definition

                            # print(_func.source_mapping.to_json()['filename_absolute'])
                            # print(_func.source_mapping[0]['source_mapping'])
                            info = [
                                "[1] arbitary calldata found in ",
                                _func,
                                "@" * 4,
                                _func.source_mapping.to_json()["filename_absolute"],
                                "\n",
                            ]
                            res = self.generate_result(info)
                            self.results.append(res)
                        _visited[_func] = self.answer
        return _visited[_func]

    def _detect(self):
        # None: there is no call() or delegatecall()
        # True: there is call or delegatecall() and data is verified
        # False: there is call or delegatecall() but data is unverified
        self.answer = None

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
                    function.name == "constructor"
                    or function._is_constructor
                    or function._visibility in ["internal", "private"]
                ):
                    continue

                self.access_control = False
                self.explore(contract, function, {}, set())

        return self.results
