import json
from collections import defaultdict
from typing import Dict, List, Set, Tuple, NamedTuple, Union

from slither.analyses.data_dependency.data_dependency import is_dependent
from slither.core.cfg.node import Node
from slither.core.declarations import Enum, Function, Contract
from slither.core.declarations.solidity_variables import (
    SolidityVariableComposed,
    SolidityFunction,
    SolidityVariable,
)
from slither.core.expressions import NewContract
from slither.core.slither_core import SlitherCore
from slither.core.solidity_types import TypeAlias
from slither.core.variables.state_variable import StateVariable
from slither.core.variables.variable import Variable
from slither.printers.abstract_printer import AbstractPrinter
from slither.slithir.operations import (
    Member,
    Operation,
    SolidityCall,
    LowLevelCall,
    HighLevelCall,
    EventCall,
    Send,
    Transfer,
    InternalDynamicCall,
    InternalCall,
    TypeConversion,
)
from slither.slithir.operations.binary import Binary
from slither.slithir.variables import Constant, ReferenceVariable
from slither.utils.output import Output
from slither.visitors.expression.constants_folding import ConstantFolding, NotConstant


def _get_name(f: Union[Function, Variable]) -> str:
    # Return the name of the function or variable
    if isinstance(f, Function):
        if f.is_fallback or f.is_receive:
            return "()"
    return f.solidity_signature


def _extract_payable(contracts: List[Contract]) -> Dict[str, List[str]]:
    ret: Dict[str, List[str]] = {}
    for contract in contracts:
        payable_functions = [_get_name(f) for f in contract.functions_entry_points if f.payable]
        if payable_functions:
            ret[contract.name] = payable_functions
    return ret


def _extract_solidity_variable_usage(
    contracts: List[Contract], sol_var: SolidityVariable
) -> Dict[str, List[str]]:
    ret: Dict[str, List[str]] = {}
    for contract in contracts:
        functions_using_sol_var = []
        for f in contract.functions_entry_points:
            for v in f.all_solidity_variables_read():
                if v == sol_var:
                    functions_using_sol_var.append(_get_name(f))
                    break
        if functions_using_sol_var:
            ret[contract.name] = functions_using_sol_var
    return ret


def _is_constant(f: Function) -> bool:  # pylint: disable=too-many-branches
    """
    Heuristic:
    - If view/pure with Solidity >= 0.4 -> Return true
    - If it contains assembly -> Return false (SlitherCore doesn't analyze asm)
    - Otherwise check for the rules from
    https://solidity.readthedocs.io/en/v0.5.0/contracts.html?highlight=pure#view-functions
    with an exception: internal dynamic call are not correctly handled, so we consider them as non-constant
    :param f:
    :return:
    """
    if f.view or f.pure:
        if not f.compilation_unit.solc_version.startswith("0.4"):
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
        if isinstance(ir, SolidityCall) and ir.function in [
            SolidityFunction("selfdestruct(address)"),
            SolidityFunction("suicide(address)"),
        ]:
            return False
        if isinstance(ir, HighLevelCall):
            if isinstance(ir.function, Variable) or ir.function.view or ir.function.pure:
                # External call to constant functions are ensured to be constant only for solidity >= 0.5
                if f.compilation_unit.solc_version.startswith("0.4"):
                    return False
            else:
                return False
        if isinstance(ir, InternalCall) and ir.function:
            # Storage write are not properly handled by all_state_variables_written
            if any(parameter.is_storage for parameter in ir.function.parameters):
                return False
    return True


def _extract_constant_functions(contracts: List[Contract]) -> Dict[str, List[str]]:
    ret: Dict[str, List[str]] = {}
    for contract in contracts:
        cst_functions = [_get_name(f) for f in contract.functions_entry_points if _is_constant(f)]
        cst_functions += [
            v.solidity_signature for v in contract.state_variables if v.visibility in ["public"]
        ]
        if cst_functions:
            ret[contract.name] = cst_functions
    return ret


def _extract_assert(contracts: List[Contract]) -> Dict[str, Dict[str, List[Dict]]]:
    """
    Return the list of contract -> function name -> List(source mapping of the assert))

    Args:
        contracts: list of contracts

    Returns:

    """
    ret: Dict[str, Dict[str, List[Dict]]] = {}
    for contract in contracts:
        functions_using_assert = []  # Dict[str, List[Dict]] = defaultdict(list)
        for f in contract.functions_entry_points:
            for v in f.all_solidity_calls():
                if v == SolidityFunction("assert(bool)"):
                    functions_using_assert.append(_get_name(f))
                    break
            # Revert https://github.com/crytic/slither/pull/2105 until format is supported by echidna.
            # for node in f.all_nodes():
            #     if SolidityFunction("assert(bool)") in node.solidity_calls and node.source_mapping:
            #         func_name = _get_name(f)
            #         functions_using_assert[func_name].append(node.source_mapping.to_json())
        if functions_using_assert:
            ret[contract.name] = functions_using_assert
    return ret


# Create a named tuple that is serialization in json
def json_serializable(cls):
    # pylint: disable=unnecessary-comprehension
    # TODO: the next line is a quick workaround to prevent pylint from crashing
    # It can be removed once https://github.com/PyCQA/pylint/pull/3810 is merged
    my_super = super

    def as_dict(self):
        yield {
            name: value for name, value in zip(self._fields, iter(my_super(cls, self).__iter__()))
        }

    cls.__iter__ = as_dict
    return cls


@json_serializable
class ConstantValue(NamedTuple):  # pylint: disable=inherit-non-class,too-few-public-methods
    # Here value should be  Union[str, int, bool]
    # But the json lib in Echidna does not handle large integer in json
    # So we convert everything to string
    value: str
    type: str


def _extract_constants_from_irs(  # pylint: disable=too-many-branches,too-many-nested-blocks
    irs: List[Operation],
    all_cst_used: List[ConstantValue],
    all_cst_used_in_binary: Dict[str, List[ConstantValue]],
    context_explored: Set[Node],
) -> None:
    for ir in irs:
        if isinstance(ir, Binary):
            for r in ir.read:
                if isinstance(r, Constant):
                    all_cst_used_in_binary[str(ir.type)].append(
                        ConstantValue(str(r.value), str(r.type))
                    )
                if isinstance(ir.variable_left, Constant) or isinstance(
                    ir.variable_right, Constant
                ):
                    if ir.lvalue:
                        try:
                            type_ = ir.lvalue.type
                            cst = ConstantFolding(ir.expression, type_).result()
                            all_cst_used.append(ConstantValue(str(cst.value), str(type_)))
                        except NotConstant:
                            pass
        if isinstance(ir, TypeConversion):
            if isinstance(ir.variable, Constant):
                if isinstance(ir.type, TypeAlias):
                    value_type = ir.type.type
                else:
                    value_type = ir.type
                all_cst_used.append(ConstantValue(str(ir.variable.value), str(value_type)))
                continue
        if (
            isinstance(ir, Member)
            and isinstance(ir.variable_left, Enum)
            and isinstance(ir.variable_right, Constant)
        ):
            # enums are constant values
            try:
                internal_num = ir.variable_left.values.index(ir.variable_right.value)
                all_cst_used.append(ConstantValue(str(internal_num), "uint256"))
            except ValueError:  # index could fail; should never happen in working solidity code
                pass
        for r in ir.read:
            var_read = r.points_to_origin if isinstance(r, ReferenceVariable) else r
            # Do not report struct_name in a.struct_name
            if isinstance(ir, Member):
                continue
            if isinstance(var_read, Constant):
                all_cst_used.append(ConstantValue(str(var_read.value), str(var_read.type)))
            if isinstance(var_read, StateVariable):
                if var_read.node_initialization:
                    if var_read.node_initialization.irs:
                        if var_read.node_initialization in context_explored:
                            continue
                        context_explored.add(var_read.node_initialization)
                        _extract_constants_from_irs(
                            var_read.node_initialization.irs,
                            all_cst_used,
                            all_cst_used_in_binary,
                            context_explored,
                        )


def _extract_constants(
    contracts: List[Contract],
) -> Tuple[Dict[str, Dict[str, List]], Dict[str, Dict[str, Dict]]]:
    # contract -> function -> [ {"value": value, "type": type} ]
    ret_cst_used: Dict[str, Dict[str, List[ConstantValue]]] = defaultdict(dict)
    # contract -> function -> binary_operand -> [ {"value": value, "type": type ]
    ret_cst_used_in_binary: Dict[str, Dict[str, Dict[str, List[ConstantValue]]]] = defaultdict(dict)
    for contract in contracts:
        for function in contract.functions_entry_points:
            all_cst_used: List = []
            all_cst_used_in_binary: Dict = defaultdict(list)

            context_explored = set()
            context_explored.add(function)
            _extract_constants_from_irs(
                function.all_slithir_operations(),
                all_cst_used,
                all_cst_used_in_binary,
                context_explored,
            )

            # Note: use list(set()) instead of set
            # As this is meant to be serialized in JSON, and JSON does not support set
            if all_cst_used:
                ret_cst_used[contract.name][_get_name(function)] = list(set(all_cst_used))
            if all_cst_used_in_binary:
                ret_cst_used_in_binary[contract.name][_get_name(function)] = {
                    k: list(set(v)) for k, v in all_cst_used_in_binary.items()
                }
    return ret_cst_used, ret_cst_used_in_binary


def _extract_function_relations(
    contracts: List[Contract],
) -> Dict[str, Dict[str, Dict[str, List[str]]]]:
    # contract -> function -> [functions]
    ret: Dict[str, Dict[str, Dict[str, List[str]]]] = defaultdict(dict)
    for contract in contracts:
        ret[contract.name] = defaultdict(dict)
        written = {
            _get_name(function): function.all_state_variables_written()
            for function in contract.functions_entry_points
        }
        read = {
            _get_name(function): function.all_state_variables_read()
            for function in contract.functions_entry_points
        }
        for function in contract.functions_entry_points:
            ret[contract.name][_get_name(function)] = {
                "impacts": [],
                "is_impacted_by": [],
            }
            for candidate, varsWritten in written.items():
                if any((r in varsWritten for r in function.all_state_variables_read())):
                    ret[contract.name][_get_name(function)]["is_impacted_by"].append(candidate)
            for candidate, varsRead in read.items():
                if any((r in varsRead for r in function.all_state_variables_written())):
                    ret[contract.name][_get_name(function)]["impacts"].append(candidate)
    return ret


def _have_external_calls(contracts: List[Contract]) -> Dict[str, List[str]]:
    """
    Detect the functions with external calls
    :param slither:
    :return:
    """
    ret: Dict[str, List[str]] = defaultdict(list)
    for contract in contracts:
        for function in contract.functions_entry_points:
            if function.all_high_level_calls() or function.all_low_level_calls():
                ret[contract.name].append(_get_name(function))
        if contract.name in ret:
            ret[contract.name] = list(set(ret[contract.name]))
    return ret


def _use_balance(contracts: List[Contract]) -> Dict[str, List[str]]:
    """
    Detect the functions with external calls
    :param slither:
    :return:
    """
    ret: Dict[str, List[str]] = defaultdict(list)
    for contract in contracts:
        for function in contract.functions_entry_points:
            for ir in function.all_slithir_operations():
                if isinstance(ir, SolidityCall) and ir.function == SolidityFunction(
                    "balance(address)"
                ):
                    ret[contract.name].append(_get_name(function))
        if contract.name in ret:
            ret[contract.name] = list(set(ret[contract.name]))
    return ret


def _with_fallback(contracts: List[Contract]) -> Set[str]:
    ret: Set[str] = set()
    for contract in contracts:
        for function in contract.functions_entry_points:
            if function.is_fallback:
                ret.add(contract.name)
    return ret


def _with_receive(contracts: List[Contract]) -> Set[str]:
    ret: Set[str] = set()
    for contract in contracts:
        for function in contract.functions_entry_points:
            if function.is_receive:
                ret.add(contract.name)
    return ret


def _call_a_parameter(slither: SlitherCore, contracts: List[Contract]) -> Dict[str, List[Dict]]:
    """
    Detect the functions with external calls
    :param slither:
    :return:
    """
    # contract -> [ (function, idx, interface_called) ]
    ret: Dict[str, List[Dict]] = defaultdict(list)
    for contract in contracts:  # pylint: disable=too-many-nested-blocks
        for function in contract.functions_entry_points:
            try:
                for ir in function.all_slithir_operations():
                    if isinstance(ir, HighLevelCall):
                        for idx, parameter in enumerate(function.parameters):
                            if is_dependent(ir.destination, parameter, function):
                                ret[contract.name].append(
                                    {
                                        "function": _get_name(function),
                                        "parameter_idx": idx,
                                        "signature": _get_name(ir.function),
                                    }
                                )
                    if isinstance(ir, LowLevelCall):
                        for idx, parameter in enumerate(function.parameters):
                            if is_dependent(ir.destination, parameter, function):
                                ret[contract.name].append(
                                    {
                                        "function": _get_name(function),
                                        "parameter_idx": idx,
                                        "signature": None,
                                    }
                                )
            except Exception as e:
                if slither.no_fail:
                    continue
                raise e
    return ret


class Echidna(AbstractPrinter):
    ARGUMENT = "echidna"
    HELP = "Export Echidna guiding information"

    WIKI = "https://github.com/trailofbits/slither/wiki/Printer-documentation#echidna"

    def output(self, filename: str) -> Output:  # pylint: disable=too-many-locals
        """
        Output the inheritance relation

        _filename is not used
        Args:
            _filename(string)
        """

        contracts = self.slither.contracts

        payable = _extract_payable(contracts)
        timestamp = _extract_solidity_variable_usage(
            contracts, SolidityVariableComposed("block.timestamp")
        )
        block_number = _extract_solidity_variable_usage(
            contracts, SolidityVariableComposed("block.number")
        )
        msg_sender = _extract_solidity_variable_usage(
            contracts, SolidityVariableComposed("msg.sender")
        )
        msg_gas = _extract_solidity_variable_usage(contracts, SolidityVariableComposed("msg.gas"))
        assert_usage = _extract_assert(contracts)
        cst_functions = _extract_constant_functions(contracts)
        (cst_used, cst_used_in_binary) = _extract_constants(contracts)

        functions_relations = _extract_function_relations(contracts)

        constructors = {
            contract.name: contract.constructor.full_name
            for contract in contracts
            if contract.constructor
        }

        external_calls = _have_external_calls(contracts)

        # call_parameters = _call_a_parameter(self.slither, contracts)

        use_balance = _use_balance(contracts)

        with_fallback = list(_with_fallback(contracts))

        with_receive = list(_with_receive(contracts))

        d = {
            "payable": payable,
            "timestamp": timestamp,
            "block_number": block_number,
            "msg_sender": msg_sender,
            "msg_gas": msg_gas,
            "assert": assert_usage,
            "constant_functions": cst_functions,
            "constants_used": cst_used,
            "constants_used_in_binary": cst_used_in_binary,
            "functions_relations": functions_relations,
            "constructors": constructors,
            "have_external_calls": external_calls,
            # "call_a_parameter": call_parameters,
            "use_balance": use_balance,
            "solc_versions": [unit.solc_version for unit in self.slither.compilation_units],
            "with_fallback": with_fallback,
            "with_receive": with_receive,
        }

        self.info(json.dumps(d, indent=4))

        res = self.generate_output(json.dumps(d, indent=4))

        return res
