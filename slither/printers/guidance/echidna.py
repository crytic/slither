"""
"""

import json
from collections import defaultdict
from typing import Dict, List, Set, Tuple, Union, NamedTuple

from slither.core.cfg.node import Node
from slither.core.declarations import Function
from slither.core.declarations.solidity_variables import SolidityVariableComposed, SolidityFunction, SolidityVariable
from slither.core.expressions import NewContract
from slither.core.slither_core import Slither
from slither.core.variables.state_variable import StateVariable
from slither.printers.abstract_printer import AbstractPrinter
from slither.slithir.operations import Member, Operation, SolidityCall, LowLevelCall, HighLevelCall, EventCall, Send, \
    Transfer, InternalDynamicCall, InternalCall, TypeConversion
from slither.slithir.operations.binary import Binary, BinaryType
from slither.slithir.variables import Constant


def _get_name(f: Function) -> str:
    if f.is_fallback or f.is_receive:
        return f'()'
    return f.full_name


def _extract_payable(slither: Slither) -> Dict[str, List[str]]:
    ret: Dict[str, List[str]] = {}
    for contract in slither.contracts:
        payable_functions = [_get_name(f) for f in contract.functions_entry_points if f.payable]
        if payable_functions:
            ret[contract.name] = payable_functions
    return ret


def _extract_solidity_variable_usage(slither: Slither, sol_var: SolidityVariable) -> Dict[str, List[str]]:
    ret: Dict[str, List[str]] = {}
    for contract in slither.contracts:
        functions_using_sol_var = []
        for f in contract.functions_entry_points:
            for v in f.all_solidity_variables_read():
                if v == sol_var:
                    functions_using_sol_var.append(_get_name(f))
                    break
        if functions_using_sol_var:
            ret[contract.name] = functions_using_sol_var
    return ret


def _is_constant(f: Function) -> bool:
    """
    Heuristic:
    - If view/pure with Solidity >= 0.4 -> Return true
    - If it contains assembly -> Return false (Slither doesn't analyze asm)
    - Otherwise check for the rules from
    https://solidity.readthedocs.io/en/v0.5.0/contracts.html?highlight=pure#view-functions
    with an exception: internal dynamic call are not correctly handled, so we consider them as non-constant
    :param f:
    :return:
    """
    if f.view or f.pure:
        if not f.contract.slither.crytic_compile.compiler_version.version.startswith('0.4'):
            return True
    if f.payable:
        return False
    if not f.is_implemented:
        return False
    if f.contains_assembly:
        return False
    if f.all_state_variables_written():
        return False
    for ir in f.all_slithir_operations():
        if isinstance(ir, InternalDynamicCall):
            return False
        if isinstance(ir, (EventCall, NewContract, LowLevelCall, Send, Transfer)):
            return False
        if isinstance(ir, SolidityCall) and ir.function in [SolidityFunction('selfdestruct(address)'),
                                                            SolidityFunction('suicide(address)')]:
            return False
        if isinstance(ir, HighLevelCall):
            if ir.function.view or ir.function.pure:
                # External call to constant functions are ensured to be constant only for solidity >= 0.5
                if f.contract.slither.crytic_compile.compiler_version.version.startswith('0.4'):
                    return False
            else:
                return False
        if isinstance(ir, InternalCall):
            # Storage write are not properly handled by all_state_variables_written
            if any(parameter.is_storage for parameter in ir.function.parameters):
                return False
    return True


def _extract_constant_functions(slither: Slither) -> Dict[str, List[str]]:
    ret: Dict[str, List[str]] = {}
    for contract in slither.contracts:
        cst_functions = [_get_name(f) for f in contract.functions_entry_points if _is_constant(f)]
        cst_functions += [v.function_name for v in contract.state_variables if v.visibility in ['public']]
        if cst_functions:
            ret[contract.name] = cst_functions
    return ret


def _extract_assert(slither: Slither) -> Dict[str, List[str]]:
    ret: Dict[str, List[str]] = {}
    for contract in slither.contracts:
        functions_using_assert = []
        for f in contract.functions_entry_points:
            for v in f.all_solidity_calls():
                if v == SolidityFunction('assert(bool)'):
                    functions_using_assert.append(_get_name(f))
                    break
        if functions_using_assert:
            ret[contract.name] = functions_using_assert
    return ret


# Create a named tuple that is serialization in json
def json_serializable(cls):
    def as_dict(self):
        yield {name: value for name, value in zip(
            self._fields,
            iter(super(cls, self).__iter__()))}

    cls.__iter__ = as_dict
    return cls


@json_serializable
class ConstantValue(NamedTuple):
    value: Union[str, int, bool]
    type: str


def _extract_constants_from_irs(irs: List[Operation],
                                all_cst_used: List[ConstantValue],
                                all_cst_used_in_binary: Dict[str, List[ConstantValue]],
                                context_explored: Set[Node]):
    for ir in irs:
        if isinstance(ir, Binary):
            for r in ir.read:
                if isinstance(r, Constant):
                    all_cst_used_in_binary[BinaryType.str(ir.type)].append(ConstantValue(r.value, str(r.type)))
        if isinstance(ir, TypeConversion):
            if isinstance(ir.variable, Constant):
                all_cst_used.append(ConstantValue(ir.variable.value, str(ir.type)))
                continue
        for r in ir.read:
            # Do not report struct_name in a.struct_name
            if isinstance(ir, Member):
                continue
            if isinstance(r, Constant):
                all_cst_used.append(ConstantValue(r.value, str(r.type)))
            if isinstance(r, StateVariable):
                if r.node_initialization:
                    if r.node_initialization.irs:
                        if r.node_initialization in context_explored:
                            continue
                        else:
                            context_explored.add(r.node_initialization)
                            _extract_constants_from_irs(r.node_initialization.irs,
                                                        all_cst_used,
                                                        all_cst_used_in_binary,
                                                        context_explored)


def _extract_constants(slither: Slither) -> Tuple[Dict[str, Dict[str, List]], Dict[str, Dict[str, Dict]]]:
    # contract -> function -> [ {"value": value, "type": type} ]
    ret_cst_used: Dict[str, Dict[str, List[ConstantValue]]] = defaultdict(dict)
    # contract -> function -> binary_operand -> [ {"value": value, "type": type ]
    ret_cst_used_in_binary: Dict[str, Dict[str, Dict[str, List[ConstantValue]]]] = defaultdict(dict)
    for contract in slither.contracts:
        for function in contract.functions_entry_points:
            all_cst_used: List = []
            all_cst_used_in_binary: Dict = defaultdict(list)

            context_explored = set()
            context_explored.add(function)
            _extract_constants_from_irs(function.all_slithir_operations(),
                                        all_cst_used,
                                        all_cst_used_in_binary,
                                        context_explored)

            # Note: use list(set()) instead of set
            # As this is meant to be serialized in JSON, and JSON does not support set
            if all_cst_used:
                ret_cst_used[contract.name][function.full_name] = list(set(all_cst_used))
            if all_cst_used_in_binary:
                ret_cst_used_in_binary[contract.name][function.full_name] = {k: list(set(v)) for k, v in
                                                                             all_cst_used_in_binary.items()}
    return ret_cst_used, ret_cst_used_in_binary


def _extract_function_relations(slither: Slither) -> Dict[str, Dict[str, Dict[str, List[str]]]]:
    # contract -> function -> [functions]
    ret: Dict[str, Dict[str, Dict[str, List[str]]]] = defaultdict(dict)
    for contract in slither.contracts:
        ret[contract.name] = defaultdict(dict)
        written = {function.full_name: function.all_state_variables_written()
                   for function in contract.functions_entry_points}
        read = {function.full_name: function.all_state_variables_read()
                for function in contract.functions_entry_points}
        for function in contract.functions_entry_points:
            ret[contract.name][function.full_name] = {"impacts": [],
                                                      "is_impacted_by": []}
            for candidate, varsWritten in written.items():
                if any((r in varsWritten for r in function.all_state_variables_read())):
                    ret[contract.name][function.full_name]["is_impacted_by"].append(candidate)
            for candidate, varsRead in read.items():
                if any((r in varsRead for r in function.all_state_variables_written())):
                    ret[contract.name][function.full_name]["impacts"].append(candidate)
    return ret


class Echidna(AbstractPrinter):
    ARGUMENT = 'echidna'
    HELP = 'Export Echidna guiding information'

    WIKI = 'https://github.com/trailofbits/slither/wiki/Printer-documentation#echidna'

    def output(self, filename):
        """
            Output the inheritance relation

            _filename is not used
            Args:
                _filename(string)
        """

        payable = _extract_payable(self.slither)
        timestamp = _extract_solidity_variable_usage(self.slither,
                                                     SolidityVariableComposed('block.timestamp'))
        block_number = _extract_solidity_variable_usage(self.slither,
                                                        SolidityVariableComposed('block.number'))
        msg_sender = _extract_solidity_variable_usage(self.slither,
                                                      SolidityVariableComposed('msg.sender'))
        msg_gas = _extract_solidity_variable_usage(self.slither,
                                                   SolidityVariableComposed('msg.gas'))
        assert_usage = _extract_assert(self.slither)
        cst_functions = _extract_constant_functions(self.slither)
        (cst_used, cst_used_in_binary) = _extract_constants(self.slither)

        functions_relations = _extract_function_relations(self.slither)

        constructors = {contract.name: contract.constructor.full_name
                        for contract in self.slither.contracts if contract.constructor}

        d = {'payable': payable,
             'timestamp': timestamp,
             'block_number': block_number,
             'msg_sender': msg_sender,
             'msg_gas': msg_gas,
             'assert': assert_usage,
             'constant_functions': cst_functions,
             'constants_used': cst_used,
             'constants_used_in_binary': cst_used_in_binary,
             'functions_relations': functions_relations,
             'constructors': constructors}

        self.info(json.dumps(d, indent=4))

        res = self.generate_output(json.dumps(d, indent=4))

        return res
