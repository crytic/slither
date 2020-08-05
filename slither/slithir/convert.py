import logging
from typing import List

from slither.core.declarations import (Contract, Enum, Event, Function,
                                       SolidityFunction, SolidityVariable,
                                       SolidityVariableComposed, Structure)
from slither.core.expressions import Identifier, Literal
from slither.core.solidity_types import (ArrayType, ElementaryType,
                                         FunctionType, MappingType,
                                         UserDefinedType, TypeInformation)
from slither.core.solidity_types.elementary_type import Int as ElementaryTypeInt
from slither.core.solidity_types.type import Type
from slither.core.variables.variable import Variable
from slither.core.variables.state_variable import StateVariable
from slither.slithir.operations.codesize import CodeSize
from slither.slithir.variables import TupleVariable
from slither.slithir.operations import (Assignment, Balance, Binary,
                                        BinaryType, Call, Condition, Delete,
                                        EventCall, HighLevelCall, Index,
                                        InitArray, InternalCall,
                                        InternalDynamicCall, Length,
                                        LibraryCall, LowLevelCall, Member,
                                        NewArray, NewContract,
                                        NewElementaryType, NewStructure,
                                        OperationWithLValue, Push, Return,
                                        Send, SolidityCall, Transfer,
                                        TypeConversion, Unary, Unpack, Nop)
from slither.slithir.tmp_operations.argument import Argument, ArgumentType
from slither.slithir.tmp_operations.tmp_call import TmpCall
from slither.slithir.tmp_operations.tmp_new_array import TmpNewArray
from slither.slithir.tmp_operations.tmp_new_contract import TmpNewContract
from slither.slithir.tmp_operations.tmp_new_elementary_type import \
    TmpNewElementaryType
from slither.slithir.tmp_operations.tmp_new_structure import TmpNewStructure
from slither.slithir.variables import (Constant, ReferenceVariable,
                                       TemporaryVariable)
from slither.visitors.slithir.expression_to_slithir import ExpressionToSlithIR
from slither.utils.function import get_function_id
from slither.utils.type import export_nested_types_from_variable
from slither.slithir.exceptions import SlithIRError

logger = logging.getLogger('ConvertToIR')


def convert_expression(expression, node):
    # handle standlone expression
    # such as return true;
    from slither.core.cfg.node import NodeType

    if isinstance(expression, Literal) and node.type in [NodeType.IF, NodeType.IFLOOP]:
        cst = Constant(expression.value, expression.type)
        cond = Condition(cst)
        cond.set_expression(expression)
        cond.set_node(node)
        result = [cond]
        return result
    if isinstance(expression, Identifier) and node.type in [NodeType.IF, NodeType.IFLOOP]:
        cond = Condition(expression.value)
        cond.set_expression(expression)
        cond.set_node(node)
        result = [cond]
        return result

    visitor = ExpressionToSlithIR(expression, node)
    result = visitor.result()

    result = apply_ir_heuristics(result, node)

    if result:
        if node.type in [NodeType.IF, NodeType.IFLOOP]:
            assert isinstance(result[-1], (OperationWithLValue))
            cond = Condition(result[-1].lvalue)
            cond.set_expression(expression)
            cond.set_node(node)
            result.append(cond)
        elif node.type == NodeType.RETURN:
            # May return None
            if isinstance(result[-1], (OperationWithLValue)):
                r = Return(result[-1].lvalue)
                r.set_expression(expression)
                r.set_node(node)
                result.append(r)

    return result


###################################################################################
###################################################################################
# region Helpers
###################################################################################
###################################################################################

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


def get_sig(ir, name):
    '''
        Return a list of potential signature
        It is a list, as Constant variables can be converted to int256
    Args:
        ir (slithIR.operation)
    Returns:
        list(str)
    '''
    sig = '{}({})'

    # list of list of arguments
    argss = convert_arguments(ir.arguments)
    return [sig.format(name, ','.join(args)) for args in argss]


def get_canonical_names(ir, function_name, contract_name):
    '''
        Return a list of potential signature
        It is a list, as Constant variables can be converted to int256
    Args:
        ir (slithIR.operation)
    Returns:
        list(str)
    '''
    sig = '{}({})'

    # list of list of arguments
    argss = convert_arguments(ir.arguments)
    return [sig.format(f'{contract_name}.{function_name}', ','.join(args)) for args in argss]


def convert_arguments(arguments):
    argss = [[]]
    for arg in arguments:
        if isinstance(arg, (list,)):
            type_arg = '{}[{}]'.format(get_type(arg[0].type), len(arg))
        elif isinstance(arg, Function):
            type_arg = arg.signature_str
        else:
            type_arg = get_type(arg.type)
        if isinstance(arg, Constant) and arg.type == ElementaryType('uint256'):
            # If it is a constant
            # We dupplicate the existing list
            # And we add uint256 and int256 cases
            # There is no potential collision, as the compiler
            # Prevent it with a 
            # "not unique after argument-dependent loopkup" issue
            argss_new = [list(args) for args in argss]
            for args in argss:
                args.append(str(ElementaryType('uint256')))
            for args in argss_new:
                args.append(str(ElementaryType('int256')))
            argss = argss + argss_new
        else:
            for args in argss:
                args.append(type_arg)
    return argss


def is_temporary(ins):
    return isinstance(ins, (Argument,
                            TmpNewElementaryType,
                            TmpNewContract,
                            TmpNewArray,
                            TmpNewStructure))


# endregion
###################################################################################
###################################################################################
# region Calls modification
###################################################################################
###################################################################################

def integrate_value_gas(result):
    '''
        Integrate value and gas temporary arguments to call instruction
    '''
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
            if is_value(ins) and isinstance(result[idx - 1], Argument):
                was_changed = True
                result[idx - 1].set_type(ArgumentType.VALUE)
                result[idx - 1].call_id = ins.ori.variable_left.name
                calls.append(ins.ori.variable_left)
                to_remove.append(ins)
                variable_to_replace[ins.lvalue.name] = ins.ori.variable_left
            elif is_gas(ins) and isinstance(result[idx - 1], Argument):
                was_changed = True
                result[idx - 1].set_type(ArgumentType.GAS)
                result[idx - 1].call_id = ins.ori.variable_left.name
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
        idx = idx + 1

    return result


# endregion
###################################################################################
###################################################################################
# region Calls modification and Type propagation
###################################################################################
###################################################################################

def propagate_type_and_convert_call(result, node):
    '''
        Propagate the types variables and convert tmp call to real call operation
    '''
    calls_value = {}
    calls_gas = {}

    call_data = []

    idx = 0
    # use of while len() as result can be modified during the iteration
    while idx < len(result):
        ins = result[idx]

        if isinstance(ins, TmpCall):
            new_ins = extract_tmp_call(ins, node.function.contract)
            if new_ins:
                new_ins.set_node(ins.node)
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

        if isinstance(ins, (HighLevelCall, NewContract, InternalDynamicCall)):
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
                if len(new_ins) == 2:
                    new_ins[0].set_node(ins.node)
                    new_ins[1].set_node(ins.node)
                    del result[idx]
                    result.insert(idx, new_ins[0])
                    result.insert(idx + 1, new_ins[1])
                    idx = idx + 1
                elif len(new_ins) == 3:
                    new_ins[0].set_node(ins.node)
                    new_ins[1].set_node(ins.node)
                    new_ins[2].set_node(ins.node)
                    del result[idx]
                    result.insert(idx, new_ins[0])
                    result.insert(idx + 1, new_ins[1])
                    result.insert(idx + 2, new_ins[2])
                    idx = idx + 2
                else:
                    # Pop conversion
                    assert len(new_ins) == 6
                    new_ins[0].set_node(ins.node)
                    new_ins[1].set_node(ins.node)
                    new_ins[2].set_node(ins.node)
                    new_ins[3].set_node(ins.node)
                    new_ins[4].set_node(ins.node)
                    new_ins[5].set_node(ins.node)
                    del result[idx]
                    result.insert(idx, new_ins[0])
                    result.insert(idx + 1, new_ins[1])
                    result.insert(idx + 2, new_ins[2])
                    result.insert(idx + 3, new_ins[3])
                    result.insert(idx + 4, new_ins[4])
                    result.insert(idx + 5, new_ins[5])
                    idx = idx + 5
            else:
                new_ins.set_node(ins.node)
                result[idx] = new_ins
        idx = idx + 1
    return result


def _convert_type_contract(ir, slither):
    assert isinstance(ir.variable_left.type, TypeInformation)
    contract = ir.variable_left.type.type

    if ir.variable_right == 'creationCode':
        if slither.crytic_compile:
            bytecode = slither.crytic_compile.bytecode_init(contract.name)
        else:
            logger.info(
                'The codebase uses type(x).creationCode, but crytic-compile was not used. As a result, the bytecode cannot be found')
            bytecode = "MISSING_BYTECODE"
        assignment = Assignment(ir.lvalue,
                                Constant(str(bytecode)),
                                ElementaryType('bytes'))
        assignment.set_expression(ir.expression)
        assignment.set_node(ir.node)
        assignment.lvalue.set_type(ElementaryType('bytes'))
        return assignment
    if ir.variable_right == 'runtimeCode':
        if slither.crytic_compile:
            bytecode = slither.crytic_compile.bytecode_runtime(contract.name)
        else:
            logger.info(
                'The codebase uses type(x).runtimeCode, but crytic-compile was not used. As a result, the bytecode cannot be found')
            bytecode = "MISSING_BYTECODE"
        assignment = Assignment(ir.lvalue,
                                Constant(str(bytecode)),
                                ElementaryType('bytes'))
        assignment.set_expression(ir.expression)
        assignment.set_node(ir.node)
        assignment.lvalue.set_type(ElementaryType('bytes'))
        return assignment
    if ir.variable_right == 'interfaceId':
        entry_points = contract.functions_entry_points
        interfaceId = 0
        for entry_point in entry_points:
            interfaceId = interfaceId ^ get_function_id(entry_point.full_name)
        assignment = Assignment(ir.lvalue,
                                Constant(str(interfaceId), type=ElementaryType('bytes4')),
                                ElementaryType('bytes4'))
        assignment.set_expression(ir.expression)
        assignment.set_node(ir.node)
        assignment.lvalue.set_type(ElementaryType('bytes4'))
        return assignment

    if ir.variable_right == 'name':
        assignment = Assignment(ir.lvalue,
                                Constant(contract.name),
                                ElementaryType('string'))
        assignment.set_expression(ir.expression)
        assignment.set_node(ir.node)
        assignment.lvalue.set_type(ElementaryType('string'))
        return assignment

    raise SlithIRError(f'type({contract.name}).{ir.variable_right} is unknown')


def propagate_types(ir, node):
    # propagate the type
    using_for = node.function.contract.using_for
    if isinstance(ir, OperationWithLValue):
        # Force assignment in case of missing previous correct type
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

                if isinstance(t, ElementaryType) and t.name == 'address':
                    if can_be_solidity_func(ir):
                        return convert_to_solidity_func(ir)

                # convert library
                if t in using_for or '*' in using_for:
                    new_ir = convert_to_library(ir, node, using_for)
                    if new_ir:
                        return new_ir

                if isinstance(t, UserDefinedType):
                    # UserdefinedType
                    t_type = t.type
                    if isinstance(t_type, Contract):
                        contract = node.slither.get_contract_from_name(t_type.name)
                        return convert_type_of_high_and_internal_level_call(ir, contract)

                # Convert HighLevelCall to LowLevelCall
                if isinstance(t, ElementaryType) and t.name == 'address':
                    if ir.destination.name == 'this':
                        return convert_type_of_high_and_internal_level_call(ir, node.function.contract)
                    if can_be_low_level(ir):
                        return convert_to_low_level(ir)

                # Convert push operations
                # May need to insert a new operation
                # Which leads to return a list of operation
                if isinstance(t, ArrayType) or (isinstance(t, ElementaryType) and t.type == 'bytes'):
                    if ir.function_name == 'push' and len(ir.arguments) == 1:
                        return convert_to_push(ir, node)
                    if ir.function_name == 'pop' and len(ir.arguments) == 0:
                        return convert_to_pop(ir, node)

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
                if ir.function is None:
                    convert_type_of_high_and_internal_level_call(ir, node.function.contract)
                return_type = ir.function.return_type
                if return_type:
                    if len(return_type) == 1:
                        ir.lvalue.set_type(return_type[0])
                    elif len(return_type) > 1:
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
                # TODO we should convert the reference to a temporary if the member is a length or a balance
                if ir.variable_right == 'length' and not isinstance(ir.variable_left, Contract) and isinstance(
                        ir.variable_left.type, (ElementaryType, ArrayType)):
                    length = Length(ir.variable_left, ir.lvalue)
                    length.set_expression(ir.expression)
                    length.lvalue.points_to = ir.variable_left
                    length.set_node(ir.node)
                    return length
                if ir.variable_right == 'balance' and not isinstance(ir.variable_left, Contract) and isinstance(
                        ir.variable_left.type, ElementaryType):
                    b = Balance(ir.variable_left, ir.lvalue)
                    b.set_expression(ir.expression)
                    b.set_node(ir.node)
                    return b
                if ir.variable_right == 'codesize' and not isinstance(ir.variable_left, Contract) and isinstance(
                        ir.variable_left.type, ElementaryType):
                    b = CodeSize(ir.variable_left, ir.lvalue)
                    b.set_expression(ir.expression)
                    b.set_node(ir.node)
                    return b
                if ir.variable_right == 'selector' and isinstance(ir.variable_left.type, Function):
                    assignment = Assignment(ir.lvalue,
                                            Constant(str(get_function_id(ir.variable_left.type.full_name))),
                                            ElementaryType('bytes4'))
                    assignment.set_expression(ir.expression)
                    assignment.set_node(ir.node)
                    assignment.lvalue.set_type(ElementaryType('bytes4'))
                    return assignment
                if isinstance(ir.variable_left, TemporaryVariable) and isinstance(ir.variable_left.type,
                                                                                  TypeInformation):
                    return _convert_type_contract(ir, node.function.slither)
                left = ir.variable_left
                t = None
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
                            # Allow type propagtion as a Function
                            # Only for reference variables
                            # This allows to track the selector keyword
                            # We dont need to check for function collision, as solc prevents the use of selector
                            # if there are multiple functions with the same name
                            f = next((f for f in type_t.functions if f.name == ir.variable_right), None)
                            if f:
                                ir.lvalue.set_type(f)
                            else:
                                # Allow propgation for variable access through contract's nale
                                # like Base_contract.my_variable
                                v = next((v for v in type_t.state_variables if v.name == ir.variable_right), None)
                                if v:
                                    ir.lvalue.set_type(v.type)
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
                if ir.function.name in ['type(address)', 'type()']:
                    ir.function.return_type = [TypeInformation(ir.arguments[0])]
                return_type = ir.function.return_type
                if len(return_type) == 1:
                    ir.lvalue.set_type(return_type[0])
                elif len(return_type) > 1:
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
            elif isinstance(ir,
                            (Argument, TmpCall, TmpNewArray, TmpNewContract, TmpNewStructure, TmpNewElementaryType)):
                # temporary operation; they will be removed
                pass
            else:
                raise SlithIRError('Not handling {} during type propgation'.format(type(ir)))


def extract_tmp_call(ins, contract):
    assert isinstance(ins, TmpCall)

    if isinstance(ins.called, Variable) and isinstance(ins.called.type, FunctionType):
        call = InternalDynamicCall(ins.lvalue, ins.called, ins.called.type)
        call.set_expression(ins.expression)
        call.call_id = ins.call_id
        return call
    if isinstance(ins.ori, Member):
        # If there is a call on an inherited contract, it is an internal call or an event
        if ins.ori.variable_left in contract.inheritance + [contract]:
            if str(ins.ori.variable_right) in [f.name for f in contract.functions]:
                internalcall = InternalCall((ins.ori.variable_right, ins.ori.variable_left.name), ins.nbr_arguments,
                                            ins.lvalue, ins.type_call)
                internalcall.set_expression(ins.expression)
                internalcall.call_id = ins.call_id
                return internalcall
            if str(ins.ori.variable_right) in [f.name for f in contract.events]:
                eventcall = EventCall(ins.ori.variable_right)
                eventcall.set_expression(ins.expression)
                eventcall.call_id = ins.call_id
                return eventcall
        if isinstance(ins.ori.variable_left, Contract):
            st = ins.ori.variable_left.get_structure_from_name(ins.ori.variable_right)
            if st:
                op = NewStructure(st, ins.lvalue)
                op.set_expression(ins.expression)
                op.call_id = ins.call_id
                return op
            libcall = LibraryCall(ins.ori.variable_left, ins.ori.variable_right, ins.nbr_arguments, ins.lvalue,
                                  ins.type_call)
            libcall.set_expression(ins.expression)
            libcall.call_id = ins.call_id
            return libcall
        msgcall = HighLevelCall(ins.ori.variable_left, ins.ori.variable_right, ins.nbr_arguments, ins.lvalue,
                                ins.type_call)
        msgcall.call_id = ins.call_id

        if ins.call_gas:
            msgcall.call_gas = ins.call_gas
        if ins.call_value:
            msgcall.call_value = ins.call_value
        msgcall.set_expression(ins.expression)

        return msgcall

    if isinstance(ins.ori, TmpCall):
        r = extract_tmp_call(ins.ori, contract)
        r.set_node(ins.node)
        return r
    if isinstance(ins.called, SolidityVariableComposed):
        if str(ins.called) == 'block.blockhash':
            ins.called = SolidityFunction('blockhash(uint256)')
        elif str(ins.called) == 'this.balance':
            s = SolidityCall(SolidityFunction('this.balance()'), ins.nbr_arguments, ins.lvalue, ins.type_call)
            s.set_expression(ins.expression)
            return s

    if isinstance(ins.called, SolidityFunction):
        s = SolidityCall(ins.called, ins.nbr_arguments, ins.lvalue, ins.type_call)
        s.set_expression(ins.expression)
        return s

    if isinstance(ins.ori, TmpNewElementaryType):
        n = NewElementaryType(ins.ori.type, ins.lvalue)
        n.set_expression(ins.expression)
        return n

    if isinstance(ins.ori, TmpNewContract):
        op = NewContract(Constant(ins.ori.contract_name), ins.lvalue)
        op.set_expression(ins.expression)
        op.call_id = ins.call_id
        if ins.call_value:
            op.call_value = ins.call_value
        if ins.call_salt:
            op.call_salt = ins.call_salt
        return op

    if isinstance(ins.ori, TmpNewArray):
        n = NewArray(ins.ori.depth, ins.ori.array_type, ins.lvalue)
        n.set_expression(ins.expression)
        return n

    if isinstance(ins.called, Structure):
        op = NewStructure(ins.called, ins.lvalue)
        op.set_expression(ins.expression)
        op.call_id = ins.call_id
        op.set_expression(ins.expression)
        return op

    if isinstance(ins.called, Event):
        e = EventCall(ins.called.name)
        e.set_expression(ins.expression)
        return e

    if isinstance(ins.called, Contract):
        # Called a base constructor, where there is no constructor
        if ins.called.constructor is None:
            return Nop()
        # Case where:
        # contract A{ constructor(uint) }
        # contract B is A {}
        # contract C is B{ constructor() A(10) B() {}
        # C calls B(), which does not exist
        # Ideally we should compare here for the parameters types too
        if len(ins.called.constructor.parameters) != ins.nbr_arguments:
            return Nop()
        internalcall = InternalCall(ins.called.constructor, ins.nbr_arguments, ins.lvalue,
                                    ins.type_call)
        internalcall.call_id = ins.call_id
        internalcall.set_expression(ins.expression)
        return internalcall

    raise Exception('Not extracted {} {}'.format(type(ins.called), ins))


# endregion
###################################################################################
###################################################################################
# region Conversion operations
###################################################################################
###################################################################################

def can_be_low_level(ir):
    return ir.function_name in ['transfer',
                                'send',
                                'call',
                                'delegatecall',
                                'callcode',
                                'staticcall']


def convert_to_low_level(ir):
    """
        Convert to a transfer/send/or low level call
        The funciton assume to receive a correct IR
        The checks must be done by the caller

        Must be called after can_be_low_level
    """
    if ir.function_name == 'transfer':
        assert len(ir.arguments) == 1
        prev_ir = ir
        ir = Transfer(ir.destination, ir.arguments[0])
        ir.set_expression(prev_ir.expression)
        ir.set_node(prev_ir.node)
        return ir
    elif ir.function_name == 'send':
        assert len(ir.arguments) == 1
        prev_ir = ir
        ir = Send(ir.destination, ir.arguments[0], ir.lvalue)
        ir.set_expression(prev_ir.expression)
        ir.set_node(prev_ir.node)
        ir.lvalue.set_type(ElementaryType('bool'))
        return ir
    elif ir.function_name in ['call',
                              'delegatecall',
                              'callcode',
                              'staticcall']:
        new_ir = LowLevelCall(ir.destination,
                              ir.function_name,
                              ir.nbr_arguments,
                              ir.lvalue,
                              ir.type_call)
        new_ir.call_gas = ir.call_gas
        new_ir.call_value = ir.call_value
        new_ir.arguments = ir.arguments
        if ir.slither.solc_version >= "0.5":
            new_ir.lvalue.set_type([ElementaryType('bool'), ElementaryType('bytes')])
        else:
            new_ir.lvalue.set_type(ElementaryType('bool'))
        new_ir.set_expression(ir.expression)
        new_ir.set_node(ir.node)
        return new_ir
    raise SlithIRError('Incorrect conversion to low level {}'.format(ir))


def can_be_solidity_func(ir):
    return ir.destination.name == 'abi' and ir.function_name in ['encode',
                                                                 'encodePacked',
                                                                 'encodeWithSelector',
                                                                 'encodeWithSignature',
                                                                 'decode']


def convert_to_solidity_func(ir):
    """
    Must be called after can_be_solidity_func
    :param ir:
    :return:
    """
    call = SolidityFunction('abi.{}()'.format(ir.function_name))
    new_ir = SolidityCall(call, ir.nbr_arguments, ir.lvalue, ir.type_call)
    new_ir.arguments = ir.arguments
    new_ir.set_expression(ir.expression)
    new_ir.set_node(ir.node)
    if isinstance(call.return_type, list) and len(call.return_type) == 1:
        new_ir.lvalue.set_type(call.return_type[0])
    elif (isinstance(new_ir.lvalue, TupleVariable) and
                call == SolidityFunction("abi.decode()") and
                len(new_ir.arguments) == 2 and
                isinstance(new_ir.arguments[1], list)):
        types = [x for x in new_ir.arguments[1]]
        new_ir.lvalue.set_type(types)
    # abi.decode where the type to decode is a singleton
    # abi.decode(a, (uint))
    elif call == SolidityFunction("abi.decode()") and len(new_ir.arguments) == 2:
        # If the variable is a referenceVariable, we are lost
        # See https://github.com/crytic/slither/issues/566 for potential solutions
        if not isinstance(new_ir.arguments[1], ReferenceVariable):
            new_ir.lvalue.set_type(new_ir.arguments[1])
    else:
        new_ir.lvalue.set_type(call.return_type)
    return new_ir


def convert_to_push(ir, node):
    """
    Convert a call to a PUSH operaiton

    The funciton assume to receive a correct IR
    The checks must be done by the caller

    May necessitate to create an intermediate operation (InitArray)
    Necessitate to return the lenght (see push documentation)
    As a result, the function return may return a list
    """

    # TODO remove Push Operator, and change this to existing operators

    lvalue = ir.lvalue
    if isinstance(ir.arguments[0], list):
        ret = []

        val = TemporaryVariable(node)
        operation = InitArray(ir.arguments[0], val)
        operation.set_expression(ir.expression)
        operation.set_node(ir.node)
        ret.append(operation)

        prev_ir = ir
        ir = Push(ir.destination, val)
        ir.set_expression(prev_ir.expression)
        ir.set_node(prev_ir.node)

        length = Literal(len(operation.init_values), 'uint256')
        t = operation.init_values[0].type
        ir.lvalue.set_type(ArrayType(t, length))

        ret.append(ir)

        if lvalue:
            length = Length(ir.array, lvalue)
            length.set_expression(ir.expression)
            length.lvalue.points_to = ir.lvalue
            length.set_node(ir.node)
            ret.append(length)

        return ret

    prev_ir = ir
    ir = Push(ir.destination, ir.arguments[0])
    ir.set_expression(prev_ir.expression)
    ir.set_node(prev_ir.node)

    if lvalue:
        ret = []
        ret.append(ir)

        length = Length(ir.array, lvalue)
        length.set_expression(ir.expression)
        length.lvalue.points_to = ir.lvalue
        length.set_node(ir.node)
        ret.append(length)
        return ret

    return ir


def convert_to_pop(ir, node):
    """
    Convert pop operators
    Return a list of 6 operations
    """

    ret = []

    arr = ir.destination
    length = ReferenceVariable(node)
    length.set_type(ElementaryType('uint256'))

    ir_length = Length(arr, length)
    ir_length.set_expression(ir.expression)
    ir_length.set_node(ir.node)
    ir_length.lvalue.points_to = arr
    ret.append(ir_length)

    val = TemporaryVariable(node)

    ir_sub_1 = Binary(val, length, Constant("1", ElementaryType('uint256')), BinaryType.SUBTRACTION)
    ir_sub_1.set_expression(ir.expression)
    ir_sub_1.set_node(ir.node)
    ret.append(ir_sub_1)

    element_to_delete = ReferenceVariable(node)
    ir_assign_element_to_delete = Index(element_to_delete, arr, val, ElementaryType('uint256'))
    ir_length.lvalue.points_to = arr
    element_to_delete.set_type(ElementaryType('uint256'))
    ir_assign_element_to_delete.set_expression(ir.expression)
    ir_assign_element_to_delete.set_node(ir.node)
    ret.append(ir_assign_element_to_delete)

    ir_delete = Delete(element_to_delete, element_to_delete)
    ir_delete.set_expression(ir.expression)
    ir_delete.set_node(ir.node)
    ret.append(ir_delete)

    length_to_assign = ReferenceVariable(node)
    length_to_assign.set_type(ElementaryType('uint256'))
    ir_length = Length(arr, length_to_assign)
    ir_length.set_expression(ir.expression)
    ir_length.lvalue.points_to = arr
    ir_length.set_node(ir.node)
    ret.append(ir_length)

    ir_assign_length = Assignment(length_to_assign, val, ElementaryType('uint256'))
    ir_assign_length.set_expression(ir.expression)
    ir_assign_length.set_node(ir.node)
    ret.append(ir_assign_length)

    return ret


def look_for_library(contract, ir, node, using_for, t):
    for destination in using_for[t]:
        lib_contract = contract.slither.get_contract_from_name(str(destination))
        if lib_contract:
            lib_call = LibraryCall(lib_contract,
                                   ir.function_name,
                                   ir.nbr_arguments,
                                   ir.lvalue,
                                   ir.type_call)
            lib_call.set_expression(ir.expression)
            lib_call.set_node(ir.node)
            lib_call.call_gas = ir.call_gas
            lib_call.arguments = [ir.destination] + ir.arguments
            new_ir = convert_type_library_call(lib_call, lib_contract)
            if new_ir:
                new_ir.set_node(ir.node)
                return new_ir
    return None


def convert_to_library(ir, node, using_for):
    # We use contract_declarer, because Solidity resolve the library
    # before resolving the inheritance.
    # Though we could use .contract as libraries cannot be shadowed
    contract = node.function.contract_declarer
    t = ir.destination.type

    if t in using_for:
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


def convert_type_library_call(ir, lib_contract):
    sigs = get_sig(ir, ir.function_name)
    func = None
    for sig in sigs:
        func = lib_contract.get_function_from_signature(sig)
        if not func:
            func = lib_contract.get_state_variable_from_name(ir.function_name)
        if func:
            # stop to explore if func is found (prevent dupplicate issue)
            break
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


def _convert_to_structure_to_list(return_type: Type) -> List[Type]:
    """
    Convert structure elements types to a list of types
    Recursive function

    :param return_type:
    :return:
    """
    if isinstance(return_type, UserDefinedType) and isinstance(return_type.type, Structure):
        ret = []
        for v in return_type.type.elems_ordered:
            ret += _convert_to_structure_to_list(v.type)
        return ret
    return [return_type.type]


def convert_type_of_high_and_internal_level_call(ir, contract):
    func = None
    if isinstance(ir, InternalCall):
        sigs = get_canonical_names(ir, ir.function_name, ir.contract_name)
        for sig in sigs:
            func = contract.get_function_from_canonical_name(sig)
            if func:
                # stop to explore if func is found (prevent dupplicate issue)
                break
        if not func:
            func = contract.get_state_variable_from_name(ir.function_name)
    else:
        assert isinstance(ir, HighLevelCall)
        sigs = get_sig(ir, ir.function_name)
        for sig in sigs:
            func = contract.get_function_from_signature(sig)
            if func:
                # stop to explore if func is found (prevent dupplicate issue)
                break
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
    if not func:
        if can_be_low_level(ir):
            return convert_to_low_level(ir)
        if can_be_solidity_func(ir):
            return convert_to_solidity_func(ir)
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
        # If its a mapping or a array
        # we iterate until we find the final type
        # mapping and array can be mixed together
        # ex:
        #    mapping ( uint => mapping ( uint => uint)) my_var
        #    mapping(uint => uint)[] test;p
        if isinstance(func.type, (MappingType, ArrayType)):
            tmp = func.type
            while isinstance(tmp, (MappingType, ArrayType)):
                if isinstance(tmp, MappingType):
                    tmp = tmp.type_to
                else:
                    tmp = tmp.type
            return_type = tmp
        else:
            return_type = func.type
    if return_type:

        # If the return type is a structure, but the lvalue is a tuple
        # We convert the type of the structure to a list of element
        # TODO: explore to replace all tuple variables by structures
        if (isinstance(ir.lvalue, TupleVariable) and
                isinstance(return_type, UserDefinedType) and
                isinstance(return_type.type, Structure)):
            return_type = _convert_to_structure_to_list(return_type)

        ir.lvalue.set_type(return_type)
    else:
        ir.lvalue = None

    return None


# endregion
###################################################################################
###################################################################################
# region Points to operation
###################################################################################
###################################################################################

def find_references_origin(irs):
    """
        Make lvalue of each Index, Member operation
        points to the left variable
    """
    for ir in irs:
        if isinstance(ir, (Index, Member)):
            ir.lvalue.points_to = ir.variable_left


# endregion
###################################################################################
###################################################################################
# region Operation filtering
###################################################################################
###################################################################################

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


# endregion
###################################################################################
###################################################################################
# region Constant type conversion
###################################################################################
###################################################################################

def convert_constant_types(irs):
    """
    late conversion of uint -> type for constant (Literal)
    :param irs:
    :return:
    """
    # TODO: implement instances lookup for events, NewContract
    was_changed = True
    while was_changed:
        was_changed = False
        for ir in irs:
            if isinstance(ir, Assignment):
                if isinstance(ir.lvalue.type, ElementaryType):
                    if ir.lvalue.type.type in ElementaryTypeInt:
                        if isinstance(ir.rvalue, Function):
                            continue
                        elif isinstance(ir.rvalue, TupleVariable):
                            # TODO: fix missing Unpack conversion
                            continue
                        else:
                            if ir.rvalue.type.type != 'int256':
                                ir.rvalue.set_type(ElementaryType('int256'))
                                was_changed = True
            if isinstance(ir, Binary):
                if isinstance(ir.lvalue.type, ElementaryType):
                    if ir.lvalue.type.type in ElementaryTypeInt:
                        for r in ir.read:
                            if r.type.type != 'int256':
                                r.set_type(ElementaryType('int256'))
                                was_changed = True
            if isinstance(ir, (HighLevelCall, InternalCall)):
                func = ir.function
                if isinstance(func, StateVariable):
                    types = export_nested_types_from_variable(func)
                else:
                    if func is None:
                        # TODO: add  POP instruction
                        break
                    types = [p.type for p in func.parameters]
                for idx, arg in enumerate(ir.arguments):
                    t = types[idx]
                    if isinstance(t, ElementaryType):
                        if t.type in ElementaryTypeInt:
                            if arg.type.type != 'int256':
                                arg.set_type(ElementaryType('int256'))
                                was_changed = True
            if isinstance(ir, NewStructure):
                st = ir.structure
                for idx, arg in enumerate(ir.arguments):
                    e = st.elems_ordered[idx]
                    if isinstance(e.type, ElementaryType):
                        if e.type.type in ElementaryTypeInt:
                            if arg.type.type != 'int256':
                                arg.set_type(ElementaryType('int256'))
                                was_changed = True
            if isinstance(ir, InitArray):
                if isinstance(ir.lvalue.type, ArrayType):
                    if isinstance(ir.lvalue.type.type, ElementaryType):
                        if ir.lvalue.type.type.type in ElementaryTypeInt:
                            for r in ir.read:
                                if r.type.type != 'int256':
                                    r.set_type(ElementaryType('int256'))
                                    was_changed = True


# endregion
###################################################################################
###################################################################################
# region Delete handling
###################################################################################
###################################################################################

def convert_delete(irs):
    """
    Convert the lvalue of the Delete to point to the variable removed
    This can only be done after find_references_origin is called
    :param irs:
    :return:
    """
    for ir in irs:
        if isinstance(ir, Delete):
            if isinstance(ir.lvalue, ReferenceVariable):
                ir.lvalue = ir.lvalue.points_to


# endregion
###################################################################################
###################################################################################
# region Heuristics selection
###################################################################################
###################################################################################

def apply_ir_heuristics(irs, node):
    """
        Apply a set of heuristic to improve slithIR
    """

    irs = integrate_value_gas(irs)

    irs = propagate_type_and_convert_call(irs, node)
    irs = remove_unused(irs)
    find_references_origin(irs)
    convert_constant_types(irs)
    convert_delete(irs)

    return irs
