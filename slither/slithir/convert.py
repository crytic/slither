from slither.core.declarations import (Contract, Event, SolidityFunction,
                                       SolidityVariableComposed, Structure)
from slither.core.expressions import Identifier, Literal
from slither.core.solidity_types.elementary_type import ElementaryType
from slither.core.variables.variable import Variable
from slither.slithir.operations import (Call, Condition, EventCall,
                                        HighLevelCall, InitArray, LibraryCall,
                                        LowLevelCall, Member, NewArray,
                                        NewContract, NewElementaryType,
                                        NewStructure, OperationWithLValue,
                                        Push, Return, Send, SolidityCall,
                                        Transfer)
from slither.slithir.tmp_operations.argument import Argument, ArgumentType
from slither.slithir.tmp_operations.tmp_call import TmpCall
from slither.slithir.tmp_operations.tmp_new_array import TmpNewArray
from slither.slithir.tmp_operations.tmp_new_contract import TmpNewContract
from slither.slithir.tmp_operations.tmp_new_elementary_type import \
    TmpNewElementaryType
from slither.slithir.tmp_operations.tmp_new_structure import TmpNewStructure
from slither.slithir.variables import (Constant, ReferenceVariable,
                                       TemporaryVariable, TupleVariable)
from slither.visitors.slithir.expression_to_slithir import ExpressionToSlithIR


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


    # Move the arguments operation to the call
    result = merge_call_parameters(result)

    # Remove temporary
    result = remove_temporary(result)

    result = replace_calls(result)

    result = remove_unused(result)
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

        # keep variables that are read
        # and reference that are written
        for ins in result:
            to_keep += [str(x) for x in ins.read]
            if isinstance(ins, OperationWithLValue):
                if isinstance(ins.lvalue, ReferenceVariable):
                    to_keep += [str(ins.lvalue)]

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
    reset = True
    def is_address(v):
        if v in [SolidityVariableComposed('msg.sender'),
                 SolidityVariableComposed('tx.origin')]:
            return True
        if not isinstance(v, Variable):
            return False
        if not isinstance(v.type, ElementaryType):
            return False
        return v.type.type == 'address'
    while reset:
        reset = False
        for idx in range(len(result)):
            ins = result[idx]
            if isinstance(ins, HighLevelCall):
                if ins.function_name == 'push':
                    assert len(ins.arguments) == 1
                    if isinstance(ins.arguments[0], list):
                        val = TemporaryVariable()
                        operation = InitArray(ins.arguments[0], val)
                        result.insert(idx, operation)
                        result[idx+1] = Push(ins.destination, val)
                        reset = True
                        break
                    else:
                        result[idx] = Push(ins.destination, ins.arguments[0])
                if is_address(ins.destination):
                    if ins.function_name == 'transfer':
                        assert len(ins.arguments) == 1
                        result[idx] = Transfer(ins.destination, ins.arguments[0])
                    elif ins.function_name == 'send':
                        assert len(ins.arguments) == 1
                        result[idx] = Send(ins.destination, ins.arguments[0], ins.lvalue)
                    elif ins.function_name in ['call', 'delegatecall', 'callcode']:
                        # TODO: handle name collision
                        result[idx] = LowLevelCall(ins.destination,
                                                   ins.function_name,
                                                   ins.nbr_arguments,
                                                   ins.lvalue,
                                                   ins.type_call)
                        result[idx].call_gas = ins.call_gas
                        result[idx].call_value = ins.call_value
                    # other case are library on address
    return result


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

def convert_libs(result, contract):
    using_for = contract.using_for
    for idx in range(len(result)):
        ir = result[idx]
        if isinstance(ir, HighLevelCall) and isinstance(ir.destination, Variable):
            if ir.destination.type in using_for:
                for destination in using_for[ir.destination.type]:
                    # destination is a UserDefinedType
                    destination = contract.slither.get_contract_from_name(str(destination))
                    if destination:
                        lib_call = LibraryCall(destination,
                                               ir.function_name,
                                               ir.nbr_arguments,
                                               ir.lvalue,
                                               ir.type_call)
                        lib_call.call_gas = ir.call_gas
                        lib_call.arguments = [ir.destination] + ir.arguments
                        result[idx] = lib_call
                        break
                assert destination

    return result

def convert_expression(expression, node):
    # handle standlone expression
    # such as return true;
    from slither.core.cfg.node import NodeType
    if isinstance(expression, Literal) and node.type == NodeType.RETURN:
        result =  [Return(Constant(expression.value))]
        return result
    if isinstance(expression, Identifier) and node.type == NodeType.RETURN:
        result =  [Return(expression.value)]
        return result
    visitor = ExpressionToSlithIR(expression)
    result = visitor.result()

    result = apply_ir_heuristics(result)

    result = convert_libs(result, node.function.contract)

    if result:
        if node.type in [NodeType.IF, NodeType.IFLOOP]:
            assert isinstance(result[-1], (OperationWithLValue))
            result.append(Condition(result[-1].lvalue))
        elif node.type == NodeType.RETURN:
            assert isinstance(result[-1], (OperationWithLValue))
            result.append(Return(result[-1].lvalue))

    return result
