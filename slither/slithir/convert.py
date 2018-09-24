from slither.visitors.slithir.expression_to_slithir import ExpressionToSlithIR
from slither.slithir.operations.assignment import Assignment
from slither.slithir.operations.member import Member
from slither.slithir.operations.lvalue import OperationWithLValue

from slither.slithir.operations.binary import BinaryOperation, BinaryOperationType
from slither.slithir.operations.high_level_call import HighLevelCall
from slither.slithir.operations.low_level_call import LowLevelCall
from slither.slithir.operations.solidity_call import SolidityCall
from slither.slithir.operations.library_call import LibraryCall
from slither.slithir.operations.new_elementary_type import NewElementaryType
from slither.slithir.operations.new_contract import NewContract
from slither.slithir.operations.new_structure import NewStructure
from slither.slithir.operations.new_array import NewArray
from slither.slithir.operations.event_call import EventCall
from slither.slithir.operations.push import Push
from slither.slithir.operations.push_array import PushArray

from slither.slithir.tmp_operations.tmp_call import TmpCall
from slither.slithir.tmp_operations.tmp_new_elementary_type import TmpNewElementaryType
from slither.slithir.tmp_operations.tmp_new_contract import TmpNewContract
from slither.slithir.tmp_operations.tmp_new_array import TmpNewArray
from slither.slithir.tmp_operations.tmp_new_structure import TmpNewStructure
from slither.slithir.tmp_operations.argument import ArgumentType, Argument

from slither.slithir.operations.call import Call

from slither.slithir.variables.constant import Constant
from slither.slithir.variables.temporary import TemporaryVariable
from slither.slithir.variables.reference import ReferenceVariable
from slither.slithir.variables.tuple import TupleVariable

from slither.core.variables.variable import Variable
from slither.core.declarations.solidity_variables import SolidityFunction, SolidityVariableComposed
from slither.core.declarations.event import Event
from slither.core.declarations.structure import Structure
from slither.core.declarations.contract import Contract

from slither.core.expressions.literal import Literal

def is_value(ins):
    if isinstance(ins, TmpCall):
        if isinstance(ins.ori, Member):
            if ins.ori.variable_right == 'value':
                return True
    return False

def is_gas(ins):
    if isinstance(ins, TmpCall):
        if isinstance(ins.ori, Member):
            if ins.ori.variable_right == 'gas':
                return True
    return False

def transform_calls(result):
    was_changed = True

    calls = []

    while was_changed:
        # We loop until we do not find any call to value or gas
        was_changed = False

        # Find all the assignments
        assigments = {}
        for i in result:
            if isinstance(i, OperationWithLValue):
                assigments[i.lvalue.name] = i
            if isinstance(i, TmpCall):
                if isinstance(i.called, Variable):
                    ins_ori = assigments[i.called.name]
                    i.set_ori(ins_ori)

        to_remove = []
        variable_to_replace = {}

        # Replace call to value, gas to an argument of the real call
        for idx in range(len(result)):
            ins = result[idx]
            if is_value(ins):
                was_changed = True
                result[idx-1].set_type(ArgumentType.VALUE)
                result[idx-1].call_id = ins.ori.variable_left.name
                calls.append(ins.ori.variable_left)
                to_remove.append(ins)
                variable_to_replace[ins.lvalue.name] = ins.ori.variable_left
            elif is_gas(ins):
                was_changed = True
                result[idx-1].set_type(ArgumentType.GAS)
                result[idx-1].call_id = ins.ori.variable_left.name
                calls.append(ins.ori.variable_left)
                to_remove.append(ins)
                variable_to_replace[ins.lvalue.name] = ins.ori.variable_left

        # Remove the call to value/gas instruction
        result = [i for i in result if not i in to_remove]

        # update the real call 
        for ins in result:
            if isinstance(ins, TmpCall):
                # use of while if there redirections
                while ins.called.name in variable_to_replace:
                    was_changed = True
                    ins.call_id = variable_to_replace[ins.called.name].name
                    calls.append(ins.called)
                    ins.called = variable_to_replace[ins.called.name]
            if isinstance(ins, Argument):
                while ins.call_id in variable_to_replace:
                    was_changed = True
                    ins.call_id = variable_to_replace[ins.call_id].name

    calls = list(set([str(c) for c in calls]))
    idx = 0
    calls_d = {}
    for call in calls:
        calls_d[str(call)] = idx
        idx = idx+1

    for idx in range(len(result)):
        ins = result[idx]
        if isinstance(ins, TmpCall):
            r = extract_tmp_call(ins)
            if r:
                result[idx] = r
    return result

def apply_ir_heuristics(result):
    """
        Apply a set of heuristic to improve slithIR
    """

    result = transform_calls(result)

    result = remove_unused(result)

    # Move the arguments operation to the call
    result = merge_call_parameters(result)

    # Remove temporary
    result = remove_temporary(result)


    reset_variable_number(result)

    return result

def reset_variable_number(result):
    """
        Reset the number associated to slithIR variables
    """
    variables = []
    for ins in result:
        variables += ins.read
        if isinstance(ins, OperationWithLValue):
            variables += [ins.lvalue]

    tmp_variables = [v for v in variables if isinstance(v, TemporaryVariable)]
    for idx in range(len(tmp_variables)):
        tmp_variables[idx].index = idx
    ref_variables = [v for v in variables if isinstance(v, ReferenceVariable)]
    for idx in range(len(ref_variables)):
        ref_variables[idx].index = idx
    tuple_variables = [v for v in variables if isinstance(v, TupleVariable)]
    for idx in range(len(tuple_variables)):
        tuple_variables[idx].index = idx


def merge_call_parameters(result):

    calls_value = {}
    calls_gas = {}

    call_data = []

    for ins in result:
        if isinstance(ins, Argument):
            if ins.get_type() in [ArgumentType.GAS]:
                assert not ins.call_id in calls_gas
                calls_gas[ins.call_id] = ins.argument
            elif ins.get_type() in [ArgumentType.VALUE]:
                assert not ins.call_id in calls_value
                calls_value[ins.call_id] = ins.argument
            else:
                assert ins.get_type() == ArgumentType.CALL
                call_data.append(ins.argument)

        if isinstance(ins, HighLevelCall):
            if ins.call_id in calls_value:
                ins.call_value = calls_value[ins.call_id]
            if ins.call_id in calls_gas:
                ins.call_gas = calls_gas[ins.call_id]

        if isinstance(ins, Call):
            ins.arguments = call_data
            call_data = []
    return result

def remove_temporary(result):
    result = [ins for ins in result if not isinstance(ins, (Argument,
                                                            TmpNewElementaryType,
                                                            TmpNewContract,
                                                            TmpNewArray,
                                                            TmpNewStructure))]

    return result

def remove_unused(result):

    removed = True
    while removed:
        removed = False

        to_keep = []
        to_remove = []

        for ins in result:
            to_keep += [str(x) for x in ins.read]

        for ins in result:
            if isinstance(ins, Member):
                if not ins.lvalue.name in to_keep:
                    to_remove.append(ins)
                    removed = True

        result = [i for i in result if not i in to_remove]
    return result


def replace_calls(result):
    '''
        replace call to push to a Push Operation
        Replace to call 'call' 'delegatecall', 'callcode' to an LowLevelCall
    '''
    for idx in range(len(result)):
        ins = result[idx]
        if isinstance(ins, HighLevelCall):
            if ins.function_name == 'push':
                assert len(ins.arguments) == 1
                if isinstance(ins.arguments[0], list):
                    result[idx] = PushArray(ins.destination, ins.arguments[0])
                else:
                    result[idx] = Push(ins.destination, ins.arguments[0])
            if ins.function_name in ['call', 'delegatecall', 'callcode']:
                result[idx] = LowLevelCall(ins.destination, ins.function_name, ins.nbr_arguments, ins.lvalue, ins.type_call)


def extract_tmp_call(ins):
    assert isinstance(ins, TmpCall)
    if isinstance(ins.ori, Member):
        if isinstance(ins.ori.variable_left, Contract):
            libcall = LibraryCall(ins.ori.variable_left, ins.ori.variable_right, ins.nbr_arguments, ins.lvalue, ins.type_call)
            libcall.call_id = ins.call_id
            return libcall
        else:
            msgcall = HighLevelCall(ins.ori.variable_left, ins.ori.variable_right, ins.nbr_arguments, ins.lvalue, ins.type_call)
            msgcall.call_id = ins.call_id
            return msgcall
    if isinstance(ins.ori, TmpCall):
        r = extract_tmp_call(ins.ori)
        return r
    if isinstance(ins.called, SolidityVariableComposed):
        # block.blockhash is the only variable composed which is a call
        assert str(ins.called) == 'block.blockhash'
        ins.called = SolidityFunction('blockhash(uint256)')

    if isinstance(ins.called, SolidityFunction):
        return SolidityCall(ins.called, ins.nbr_arguments, ins.lvalue, ins.type_call)

    if isinstance(ins.ori, TmpNewElementaryType):
        return NewElementaryType(ins.ori.type, ins.lvalue)

    if isinstance(ins.ori, TmpNewContract):
        return NewContract(Constant(ins.ori.contract_name), ins.lvalue)

    if isinstance(ins.ori, TmpNewArray):
        return NewArray(ins.ori.depth, ins.ori.array_type, ins.lvalue)

    if isinstance(ins.called, Structure):
        return NewStructure(ins.called, ins.lvalue)

    if isinstance(ins.called, Event):
        return EventCall(ins.called.name)

    raise Exception('Not extracted {} {}'.format(type(ins.called), ins))

def convert_expression(expression):
    # handle standlone expression
    # such as return true;
    if isinstance(expression, Literal):
        return [Constant(expression.value)]
    visitor = ExpressionToSlithIR(expression)
    result = visitor.result()

    result = apply_ir_heuristics(result)

    return result
