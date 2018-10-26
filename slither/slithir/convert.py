import logging

from slither.core.declarations import (Contract, Enum, Event, SolidityFunction,
                                       Structure, SolidityVariableComposed, Function, SolidityVariable)
from slither.core.expressions import Identifier, Literal
from slither.core.solidity_types import ElementaryType, UserDefinedType, MappingType, ArrayType, FunctionType
from slither.core.variables.variable import Variable
from slither.slithir.operations import (Assignment, Binary, BinaryType, Call,
                                        Condition, Delete, EventCall,
                                        HighLevelCall, Index, InitArray,
                                        InternalCall, InternalDynamicCall, LibraryCall,
                                        LowLevelCall, Member, NewArray,
                                        NewContract, NewElementaryType,
                                        NewStructure, OperationWithLValue,
                                        Push, Return, Send, SolidityCall,
                                        Transfer, TypeConversion, Unary,
                                        Unpack)
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

logger = logging.getLogger('ConvertToIR')

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

def integrate_value_gas(result):
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
                if isinstance(i.called, Variable) and i.called.name in assigments:
                    ins_ori = assigments[i.called.name]
                    i.set_ori(ins_ori)

        to_remove = []
        variable_to_replace = {}

        # Replace call to value, gas to an argument of the real call
        for idx in range(len(result)):
            ins = result[idx]
            # value can be shadowed, so we check that the prev ins
            # is an Argument
            if is_value(ins) and isinstance(result[idx-1], Argument):
                was_changed = True
                result[idx-1].set_type(ArgumentType.VALUE)
                result[idx-1].call_id = ins.ori.variable_left.name
                calls.append(ins.ori.variable_left)
                to_remove.append(ins)
                variable_to_replace[ins.lvalue.name] = ins.ori.variable_left
            elif is_gas(ins) and isinstance(result[idx-1], Argument):
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

    return result

def propage_type_and_convert_call(result, node):
    calls_value = {}
    calls_gas = {}

    call_data = []

    idx = 0
    # use of while len() as result can be modified during the iteration
    while idx < len(result):
        ins = result[idx]

        if isinstance(ins, TmpCall):
            new_ins = extract_tmp_call(ins)
            if new_ins:
                ins = new_ins
                result[idx] = ins

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

        if isinstance(ins, (HighLevelCall, NewContract)):
            if ins.call_id in calls_value:
                ins.call_value = calls_value[ins.call_id]
            if ins.call_id in calls_gas:
                ins.call_gas = calls_gas[ins.call_id]

        if isinstance(ins, (Call, NewContract, NewStructure)):
            ins.arguments = call_data
            call_data = []

        if is_temporary(ins):
            del result[idx]
            continue

        new_ins = propagate_types(ins, node)
        if new_ins:
            if isinstance(new_ins, (list,)):
                assert len(new_ins) == 2
                result.insert(idx, new_ins[0])
                result.insert(idx+1, new_ins[1])
                idx = idx + 1 
            else:
                result[idx] = new_ins
        idx = idx +1
    return result

def convert_to_low_level(ir):
    """
        Convert to a transfer/send/or low level call
        The funciton assume to receive a correct IR
        The checks must be done by the caller

        Additionally convert abi... to solidityfunction
    """
    if ir.function_name == 'transfer':
        assert len(ir.arguments) == 1
        ir = Transfer(ir.destination, ir.arguments[0])
        return ir
    elif ir.function_name == 'send':
        assert len(ir.arguments) == 1
        ir = Send(ir.destination, ir.arguments[0], ir.lvalue)
        ir.lvalue.set_type(ElementaryType('bool'))
        return ir
    elif ir.destination.name ==  'abi' and ir.function_name in ['encode',
                                                                'encodePacked',
                                                                'encodeWithSelector',
                                                                'encodeWithSignature']:

        call = SolidityFunction('abi.{}()'.format(ir.function_name))
        new_ir = SolidityCall(call, ir.nbr_arguments, ir.lvalue, ir.type_call)
        new_ir.arguments = ir.arguments
        new_ir.lvalue.set_type(call.return_type)
        return new_ir
    elif ir.function_name in ['call', 'delegatecall', 'callcode']:
        new_ir = LowLevelCall(ir.destination,
                          ir.function_name,
                          ir.nbr_arguments,
                          ir.lvalue,
                          ir.type_call)
        new_ir.call_gas = ir.call_gas
        new_ir.call_value = ir.call_value
        new_ir.arguments = ir.arguments
        new_ir.lvalue.set_type(ElementaryType('bool'))
        return new_ir
    logger.error('Incorrect conversion to low level {}'.format(ir))
    exit(-1)

def convert_to_push(ir):
    """
    Convert a call to a PUSH operaiton

    The funciton assume to receive a correct IR
    The checks must be done by the caller

    May necessitate to create an intermediate operation (InitArray)
    As a result, the function return may return a list
    """
    if isinstance(ir.arguments[0], list):
        ret = []

        val = TemporaryVariable()
        operation = InitArray(ir.arguments[0], val)
        ret.append(operation)

        ir = Push(ir.destination, val)

        length = Literal(len(operation.init_values))
        t = operation.init_values[0].type
        ir.lvalue.set_type(ArrayType(t, length))

        ret.append(ir)
        return ret

    ir = Push(ir.destination, ir.arguments[0])
    return ir

def look_for_library(contract, ir, node, using_for, t):
    for destination in using_for[t]:
        lib_contract = contract.slither.get_contract_from_name(str(destination))
        if lib_contract:
            lib_call = LibraryCall(lib_contract,
                                   ir.function_name,
                                   ir.nbr_arguments,
                                   ir.lvalue,
                                   ir.type_call)
            lib_call.call_gas = ir.call_gas
            lib_call.arguments = [ir.destination] + ir.arguments
            new_ir = convert_type_library_call(lib_call, lib_contract)
            if new_ir:
                return new_ir
    return None

def convert_to_library(ir, node, using_for):
    contract = node.function.contract
    t = ir.destination.type

    new_ir = look_for_library(contract, ir, node, using_for, t)
    if new_ir:
        return new_ir

    if '*' in using_for:
        new_ir = look_for_library(contract, ir, node, using_for, '*')
        if new_ir:
            return new_ir

    return None

def get_type(t):
    """
        Convert a type to a str
        If the instance is a Contract, return 'address' instead
    """
    if isinstance(t, UserDefinedType):
        if isinstance(t.type, Contract):
            return 'address'
    return str(t)

def get_sig(ir):
    sig = '{}({})'
    name = ir.function_name

    args = []
    for arg in ir.arguments:
        if isinstance(arg, (list,)):
            type_arg = '{}[{}]'.format(get_type(arg[0].type), len(arg))
        elif isinstance(arg, Function):
            type_arg = arg.signature_str
        else:
            type_arg = get_type(arg.type)
        args.append(type_arg)
    return sig.format(name, ','.join(args))

def convert_type_library_call(ir, lib_contract):
    sig = get_sig(ir)
    func = lib_contract.get_function_from_signature(sig)
    if not func:
        func = lib_contract.get_state_variable_from_name(ir.function_name)
    # In case of multiple binding to the same type
    if not func:
        # specific lookup when the compiler does implicit conversion
        # for example
        # myFunc(uint)
        # can be called with an uint8
        for function in lib_contract.functions:
            if function.name == ir.function_name and len(function.parameters) == len(ir.arguments):
                func = function
                break
    if not func:
        return None
    ir.function = func
    if isinstance(func, Function):
        t = func.return_type
        # if its not a tuple, return a singleton
        if t and len(t) == 1:
            t = t[0]
    else:
        # otherwise its a variable (getter)
        t = func.type
    if t:
        ir.lvalue.set_type(t)
    else:
        ir.lvalue = None
    return ir

def convert_type_of_high_level_call(ir, contract):
    sig = get_sig(ir)
    func = contract.get_function_from_signature(sig)
    if not func:
        func = contract.get_state_variable_from_name(ir.function_name)
    if not func:
        # specific lookup when the compiler does implicit conversion
        # for example
        # myFunc(uint)
        # can be called with an uint8
        for function in contract.functions:
            if function.name == ir.function_name and len(function.parameters) == len(ir.arguments):
                func = function
                break
    # lowlelvel lookup needs to be done at last step
    if not func and ir.function_name in ['call',
                                         'delegatecall',
                                         'codecall',
                                         'transfer',
                                         'send']:
        return convert_to_low_level(ir)
    if not func:
        logger.error('Function not found {}'.format(sig))
    ir.function = func
    if isinstance(func, Function):
        return_type = func.return_type
        # if its not a tuple; return a singleton
        if return_type and len(return_type) == 1:
            return_type = return_type[0]
    else:
        # otherwise its a variable (getter)
        return_type = func.type
    if return_type:
        ir.lvalue.set_type(return_type)
    else:
        ir.lvalue = None

    return None

def propagate_types(ir, node):
    # propagate the type
    using_for = node.function.contract.using_for
    if isinstance(ir, OperationWithLValue):
        if not ir.lvalue.type:
            if isinstance(ir, Assignment):
                ir.lvalue.set_type(ir.rvalue.type)
            elif isinstance(ir, Binary):
                if BinaryType.return_bool(ir.type):
                    ir.lvalue.set_type(ElementaryType('bool'))
                else:
                    ir.lvalue.set_type(ir.variable_left.type)
            elif isinstance(ir, Delete):
                # nothing to propagate
                pass
            elif isinstance(ir, LibraryCall):
                return convert_type_library_call(ir, ir.destination)
            elif isinstance(ir, HighLevelCall):
                t = ir.destination.type

                # Temporary operation (they are removed later)
                if t is None:
                    return

                # convert library
                if t in using_for:
                    new_ir = convert_to_library(ir, node, using_for)
                    if new_ir:
                        return new_ir

                if isinstance(t, UserDefinedType):
                    # UserdefinedType
                    t_type = t.type
                    if isinstance(t_type, Contract):
                        contract = node.slither.get_contract_from_name(t_type.name)
                        return convert_type_of_high_level_call(ir, contract)

                # Convert HighLevelCall to LowLevelCall
                if isinstance(t, ElementaryType) and t.name == 'address':
                    if ir.destination.name == 'this':
                        return convert_type_of_high_level_call(ir, node.function.contract)
                    return convert_to_low_level(ir)

                # Convert push operations
                # May need to insert a new operation
                # Which leads to return a list of operation
                if isinstance(t, ArrayType):
                    if ir.function_name == 'push' and len(ir.arguments) == 1:
                        return convert_to_push(ir)

            elif isinstance(ir, Index):
                if isinstance(ir.variable_left.type, MappingType):
                    ir.lvalue.set_type(ir.variable_left.type.type_to)
                elif isinstance(ir.variable_left.type, ArrayType):
                    ir.lvalue.set_type(ir.variable_left.type.type)

            elif isinstance(ir, InitArray):
                length = len(ir.init_values)
                t = ir.init_values[0].type
                ir.lvalue.set_type(ArrayType(t, length))
            elif isinstance(ir, InternalCall):
                # if its not a tuple, return a singleton
                return_type = ir.function.return_type
                if return_type:
                    if len(return_type) == 1:
                        ir.lvalue.set_type(return_type[0])
                    else:
                        ir.lvalue.set_type(return_type)
                else:
                    ir.lvalue = None
            elif isinstance(ir, InternalDynamicCall):
                # if its not a tuple, return a singleton
                return_type = ir.function_type.return_type
                if return_type:
                    if len(return_type) == 1:
                        ir.lvalue.set_type(return_type[0])
                    else:
                        ir.lvalue.set_type(return_type)
                else:
                    ir.lvalue = None
            elif isinstance(ir, LowLevelCall):
                # Call are not yet converted
                # This should not happen
                assert False
            elif isinstance(ir, Member):
                left = ir.variable_left
                if isinstance(left, (Variable, SolidityVariable)):
                    t = ir.variable_left.type
                elif isinstance(left, (Contract, Enum, Structure)):
                    t = UserDefinedType(left)
                # can be None due to temporary operation
                if t:
                    if isinstance(t, UserDefinedType):
                        # UserdefinedType
                        type_t = t.type
                        if isinstance(type_t, Enum):
                            ir.lvalue.set_type(t)
                        elif isinstance(type_t, Structure):
                            elems = type_t.elems
                            for elem in elems:
                                if elem == ir.variable_right:
                                    ir.lvalue.set_type(elems[elem].type)
                        else:
                            assert isinstance(type_t, Contract)
            elif isinstance(ir, NewArray):
                ir.lvalue.set_type(ir.array_type)
            elif isinstance(ir, NewContract):
                contract = node.slither.get_contract_from_name(ir.contract_name)
                ir.lvalue.set_type(UserDefinedType(contract))
            elif isinstance(ir, NewElementaryType):
                ir.lvalue.set_type(ir.type)
            elif isinstance(ir, NewStructure):
                ir.lvalue.set_type(UserDefinedType(ir.structure))
            elif isinstance(ir, Push):
                # No change required
                pass
            elif isinstance(ir, Send):
                ir.lvalue.set_type(ElementaryType('bool'))
            elif isinstance(ir, SolidityCall):
                return_type = ir.function.return_type
                if len(return_type) == 1:
                    ir.lvalue.set_type(return_type[0])
                else:
                    ir.lvalue.set_type(return_type)
            elif isinstance(ir, TypeConversion):
                ir.lvalue.set_type(ir.type)
            elif isinstance(ir, Unary):
                ir.lvalue.set_type(ir.rvalue.type)
            elif isinstance(ir, Unpack):
                types = ir.tuple.type.type
                idx = ir.index
                t = types[idx]
                ir.lvalue.set_type(t)
            elif isinstance(ir, (Argument, TmpCall, TmpNewArray, TmpNewContract, TmpNewStructure, TmpNewElementaryType)):
                # temporary operation; they will be removed
                pass
            else:
                logger.error('Not handling {} during type propgation'.format(type(ir)))
                exit(-1)

def apply_ir_heuristics(irs, node):
    """
        Apply a set of heuristic to improve slithIR
    """

    irs = integrate_value_gas(irs)

    irs = propage_type_and_convert_call(irs, node)
#    irs = remove_temporary(irs)
#    irs = replace_calls(irs)
    irs = remove_unused(irs)

    find_references_origin(irs)

    #reset_variable_number(irs)

    return irs

def find_references_origin(irs):
    """
        Make lvalue of each Index, Member operation
        points to the left variable
    """
    for ir in irs:
        if isinstance(ir, (Index, Member)):
            ir.lvalue.points_to = ir.variable_left

def is_temporary(ins):
    return isinstance(ins, (Argument,
                            TmpNewElementaryType,
                            TmpNewContract,
                            TmpNewArray,
                            TmpNewStructure))


def remove_temporary(result):
    result = [ins for ins in result if not isinstance(ins, (Argument,
                                                            TmpNewElementaryType,
                                                            TmpNewContract,
                                                            TmpNewArray,
                                                            TmpNewStructure))]

    return result

def remove_unused(result):
    removed = True

    if not result:
        return result

    # dont remove the last elem, as it may be used by RETURN
    last_elem = result[-1]

    while removed:
        removed = False

        to_keep = []
        to_remove = []

        # keep variables that are read
        # and reference that are written
        for ins in result:
            to_keep += [str(x) for x in ins.read]
            if isinstance(ins, OperationWithLValue) and not isinstance(ins, (Index, Member)):
                if isinstance(ins.lvalue, ReferenceVariable):
                    to_keep += [str(ins.lvalue)]

        for ins in result:
            if isinstance(ins, Member):
                if not ins.lvalue.name in to_keep and ins != last_elem:
                    to_remove.append(ins)
                    removed = True

        result = [i for i in result if not i in to_remove]
    return result



def extract_tmp_call(ins):
    assert isinstance(ins, TmpCall)
    if isinstance(ins.ori, Member):
        if isinstance(ins.ori.variable_left, Contract):
            libcall = LibraryCall(ins.ori.variable_left, ins.ori.variable_right, ins.nbr_arguments, ins.lvalue, ins.type_call)
            libcall.call_id = ins.call_id
            return libcall
        msgcall = HighLevelCall(ins.ori.variable_left, ins.ori.variable_right, ins.nbr_arguments, ins.lvalue, ins.type_call)
        msgcall.call_id = ins.call_id
        return msgcall

    if isinstance(ins.ori, TmpCall):
        r = extract_tmp_call(ins.ori)
        return r
    if isinstance(ins.called, SolidityVariableComposed):
        if str(ins.called) == 'block.blockhash':
            ins.called = SolidityFunction('blockhash(uint256)')
        elif str(ins.called) == 'this.balance':
            return SolidityCall(SolidityFunction('this.balance()'), ins.nbr_arguments, ins.lvalue, ins.type_call)

    if isinstance(ins.called, SolidityFunction):
        return SolidityCall(ins.called, ins.nbr_arguments, ins.lvalue, ins.type_call)

    if isinstance(ins.ori, TmpNewElementaryType):
        return NewElementaryType(ins.ori.type, ins.lvalue)

    if isinstance(ins.ori, TmpNewContract):
        op = NewContract(Constant(ins.ori.contract_name), ins.lvalue)
        op.call_id = ins.call_id
        return op

    if isinstance(ins.ori, TmpNewArray):
        return NewArray(ins.ori.depth, ins.ori.array_type, ins.lvalue)

    if isinstance(ins.called, Structure):
        op = NewStructure(ins.called, ins.lvalue)
        op.call_id = ins.call_id
        return op

    if isinstance(ins.called, Event):
        return EventCall(ins.called.name)

    if isinstance(ins.called, Variable) and isinstance(ins.called.type, FunctionType):
        return InternalDynamicCall(ins.lvalue, ins.called, ins.called.type)

    raise Exception('Not extracted {} {}'.format(type(ins.called), ins))

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
    if isinstance(expression, Literal) and node.type in [NodeType.IF, NodeType.IFLOOP]:
        result =  [Condition(Constant(expression.value))]
        return result
    if isinstance(expression, Identifier) and node.type in [NodeType.IF, NodeType.IFLOOP]:
        result =  [Condition(expression.value)]
        return result
    visitor = ExpressionToSlithIR(expression)
    result = visitor.result()

    result = apply_ir_heuristics(result, node)

    if result:
        if node.type in [NodeType.IF, NodeType.IFLOOP]:
            assert isinstance(result[-1], (OperationWithLValue))
            result.append(Condition(result[-1].lvalue))
        elif node.type == NodeType.RETURN:
            # May return None
            if isinstance(result[-1], (OperationWithLValue)):
                result.append(Return(result[-1].lvalue))

    return result
