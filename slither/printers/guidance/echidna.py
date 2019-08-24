"""
"""

import json
from collections import defaultdict
from slither.printers.abstract_printer import AbstractPrinter
from slither.core.declarations.solidity_variables import SolidityVariableComposed, SolidityFunction
from slither.slithir.operations.binary import Binary, BinaryType

from slither.slithir.variables import Constant


def _extract_payable(slither):
    ret = {}
    for contract in slither.contracts:
        payable_functions = [f.full_name for f in contract.functions_entry_points if f.payable]
        if payable_functions:
            ret[contract.name] = payable_functions
    return ret

def _extract_solidity_variable_usage(slither, sol_var):
    ret = {}
    for contract in slither.contracts:
        functions_using_sol_var = []
        for f in contract.functions_entry_points:
            for v in f.all_solidity_variables_read():
                if v == sol_var:
                    functions_using_sol_var.append(f.full_name)
                    break
        if functions_using_sol_var:
            ret[contract.name] = functions_using_sol_var
    return ret

def _extract_constant_functions(slither):
    ret = {}
    for contract in slither.contracts:
        cst_functions = [f.full_name for f in contract.functions_entry_points if f.view or f.pure]
        if cst_functions:
            ret[contract.name] = cst_functions
    return ret

def _extract_assert(slither):
    ret = {}
    for contract in slither.contracts:
        functions_using_assert = []
        for f in contract.functions_entry_points:
            for v in f.all_solidity_calls():
                if v == SolidityFunction('assert(bool)'):
                    functions_using_assert.append(f.full_name)
                    break
        if functions_using_assert:
            ret[contract.name] = functions_using_assert
    return ret


def _extract_constants(slither):
    ret_cst_used = defaultdict(dict)
    ret_cst_used_in_binary = defaultdict(dict)
    for contract in slither.contracts:
        for function in contract.functions_entry_points:
            all_cst_used = []
            all_cst_used_in_binary = defaultdict(list)
            for ir in function.all_slithir_operations():
                if isinstance(ir, Binary):
                    for r in ir.read:
                        if isinstance(r, Constant):
                            all_cst_used_in_binary[BinaryType.str(ir.type)].append(r.value)
                for r in ir.read:
                    if isinstance(r, Constant):
                        all_cst_used.append(r.value)
            if all_cst_used:
                ret_cst_used[contract.name][function.full_name] = all_cst_used
            if all_cst_used_in_binary:
                ret_cst_used_in_binary[contract.name][function.full_name] = all_cst_used_in_binary
    return (ret_cst_used, ret_cst_used_in_binary)




class Echidna(AbstractPrinter):
    ARGUMENT = 'echidna'
    HELP = 'todo'

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

        print(json.dumps(d, indent=4))