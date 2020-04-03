"""
"""

import json
from collections import defaultdict
from typing import Dict, List, Set, Tuple

from slither.core.cfg.node import Node
from slither.core.declarations import Function
from slither.core.slither_core import Slither
from slither.core.variables.variable import Variable
from slither.printers.abstract_printer import AbstractPrinter
from slither.core.declarations.solidity_variables import SolidityVariableComposed, SolidityFunction, SolidityVariable
from slither.slithir.operations import Member, Operation
from slither.slithir.operations.binary import Binary, BinaryType
from slither.core.variables.state_variable import StateVariable
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


def _extract_constant_functions(slither: Slither) -> Dict[str, List[str]]:
    ret: Dict[str, List[str]] = {}
    for contract in slither.contracts:
        cst_functions = [_get_name(f) for f in contract.functions_entry_points if f.view or f.pure]
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


def _extract_constants_from_irs(irs: List[Operation],
                                all_cst_used: List,
                                all_cst_used_in_binary: Dict,
                                context_explored: Set[Node]):
    for ir in irs:
        if isinstance(ir, Binary):
            for r in ir.read:
                if isinstance(r, Constant):
                    all_cst_used_in_binary[BinaryType.str(ir.type)].append(r.value)
        for r in ir.read:
            # Do not report struct_name in a.struct_name
            if isinstance(ir, Member):
                continue
            if isinstance(r, Constant):
                all_cst_used.append(r.value)
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
    ret_cst_used: Dict[str, Dict[str, List]] = defaultdict(dict)
    ret_cst_used_in_binary: Dict[str, Dict[str, Dict]] = defaultdict(dict)
    for contract in slither.contracts:
        for function in contract.functions_entry_points:
            all_cst_used = []
            all_cst_used_in_binary = defaultdict(list)

            context_explored = set()
            context_explored.add(function)
            _extract_constants_from_irs(function.all_slithir_operations(),
                                        all_cst_used,
                                        all_cst_used_in_binary,
                                        context_explored)

            if all_cst_used:
                ret_cst_used[contract.name][function.full_name] = all_cst_used
            if all_cst_used_in_binary:
                ret_cst_used_in_binary[contract.name][function.full_name] = all_cst_used_in_binary
    return ret_cst_used, ret_cst_used_in_binary


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

        d = {'payable': payable,
             'timestamp': timestamp,
             'block_number': block_number,
             'msg_sender': msg_sender,
             'msg_gas': msg_gas,
             'assert': assert_usage,
             'constant_functions': cst_functions,
             'constants_used': cst_used,
             'constants_used_in_binary': cst_used_in_binary}

        self.info(json.dumps(d, indent=4))

        res = self.generate_output(json.dumps(d, indent=4))

        return res
