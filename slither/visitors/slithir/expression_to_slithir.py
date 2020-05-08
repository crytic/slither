import logging
from typing import List, TYPE_CHECKING

from slither.core.declarations import Function
from slither.core.expressions import (
    AssignmentOperationType,
    UnaryOperationType,
    BinaryOperationType,
)
from slither.core.expressions.expression import Expression
from slither.slithir.operations import (
    Assignment,
    Binary,
    BinaryType,
    Delete,
    Index,
    InitArray,
    InternalCall,
    AccessMember,
    NewArray,
    NewContract,
    UpdateMember,
    TypeConversion,
    Unary,
    Unpack,
    Return,
    UpdateMemberDependency,
    UpdateIndex,
    UnaryType,
    Operation,
)
from slither.slithir.tmp_operations.argument import Argument
from slither.slithir.tmp_operations.tmp_call import TmpCall
from slither.core.solidity_types.type import Type
from slither.core.solidity_types import ArrayType
from slither.slithir.tmp_operations.tmp_new_array import TmpNewArray
from slither.slithir.tmp_operations.tmp_new_contract import TmpNewContract
from slither.slithir.tmp_operations.tmp_new_elementary_type import TmpNewElementaryType
from slither.slithir.variables import (
    Constant,
    IndexVariable,
    TemporaryVariable,
    TupleVariable,
    MemberVariable,
)
from slither.visitors.expression.expression import ExpressionVisitor

from slither.slithir.exceptions import SlithIRError

if TYPE_CHECKING:
    from slither.core.cfg.node import Node

logger = logging.getLogger("VISTIOR:ExpressionToSlithIR")

key = "expressionToSlithIR"


def get(expression):
    val = expression.context[key]
    # we delete the item to reduce memory use
    del expression.context[key]
    return val


def set_val(expression, val):
    expression.context[key] = val


_assign_to_binary = {
    AssignmentOperationType.ASSIGN_MULTIPLICATION: BinaryType.MULTIPLICATION,
    AssignmentOperationType.ASSIGN_DIVISION: BinaryType.DIVISION,
    AssignmentOperationType.ASSIGN_MODULO: BinaryType.MODULO,
    AssignmentOperationType.ASSIGN_ADDITION: BinaryType.ADDITION,
    AssignmentOperationType.ASSIGN_SUBTRACTION: BinaryType.SUBTRACTION,
    AssignmentOperationType.ASSIGN_LEFT_SHIFT: BinaryType.LEFT_SHIFT,
    AssignmentOperationType.ASSIGN_RIGHT_SHIFT: BinaryType.RIGHT_SHIFT,
    AssignmentOperationType.ASSIGN_AND: BinaryType.AND,
    AssignmentOperationType.ASSIGN_CARET: BinaryType.CARET,
    AssignmentOperationType.ASSIGN_OR: BinaryType.OR,
}


_binary_to_binary = {
    BinaryOperationType.POWER: BinaryType.POWER,
    BinaryOperationType.MULTIPLICATION: BinaryType.MULTIPLICATION,
    BinaryOperationType.DIVISION: BinaryType.DIVISION,
    BinaryOperationType.MODULO: BinaryType.MODULO,
    BinaryOperationType.ADDITION: BinaryType.ADDITION,
    BinaryOperationType.SUBTRACTION: BinaryType.SUBTRACTION,
    BinaryOperationType.LEFT_SHIFT: BinaryType.LEFT_SHIFT,
    BinaryOperationType.RIGHT_SHIFT: BinaryType.RIGHT_SHIFT,
    BinaryOperationType.AND: BinaryType.AND,
    BinaryOperationType.CARET: BinaryType.CARET,
    BinaryOperationType.OR: BinaryType.OR,
    BinaryOperationType.LESS: BinaryType.LESS,
    BinaryOperationType.GREATER: BinaryType.GREATER,
    BinaryOperationType.LESS_EQUAL: BinaryType.LESS_EQUAL,
    BinaryOperationType.GREATER_EQUAL: BinaryType.GREATER_EQUAL,
    BinaryOperationType.EQUAL: BinaryType.EQUAL,
    BinaryOperationType.NOT_EQUAL: BinaryType.NOT_EQUAL,
    BinaryOperationType.ANDAND: BinaryType.ANDAND,
    BinaryOperationType.OROR: BinaryType.OROR,
}


def convert_assignement_member(left, right, t):
    operations = []

    if t == AssignmentOperationType.ASSIGN:
        operations.append(UpdateMember(left.base, left.member, right))

    elif t in _assign_to_binary:
        val = TemporaryVariable(left.node)
        operations.append(Binary(val, left, right, _assign_to_binary[t]))
        operations.append(UpdateMember(left.base, left.member, val))

    return operations, left


def convert_assignement_index(left, right, t):
    operations = []

    if t == AssignmentOperationType.ASSIGN:
        operations.append(UpdateIndex(left.base, left.offset, right))

    elif t in _assign_to_binary:
        val = TemporaryVariable(left.node)
        operations.append(Binary(val, left, right, _assign_to_binary[t]))
        operations.append(UpdateIndex(left.base, left.offset, val))

    return operations, left


def convert_assignment(left, right, t, return_type):
    if isinstance(left, MemberVariable):
        return convert_assignement_member(left, right, t)
    if isinstance(left, IndexVariable):
        return convert_assignement_index(left, right, t)

    if t == AssignmentOperationType.ASSIGN:
        return [Assignment(left, right, return_type)], left
    elif t == AssignmentOperationType.ASSIGN_OR:
        return [Binary(left, left, right, BinaryType.OR)], left
    elif t == AssignmentOperationType.ASSIGN_CARET:
        return [Binary(left, left, right, BinaryType.CARET)], left
    elif t == AssignmentOperationType.ASSIGN_AND:
        return [Binary(left, left, right, BinaryType.AND)], left
    elif t == AssignmentOperationType.ASSIGN_LEFT_SHIFT:
        return [Binary(left, left, right, BinaryType.LEFT_SHIFT)], left
    elif t == AssignmentOperationType.ASSIGN_RIGHT_SHIFT:
        return [Binary(left, left, right, BinaryType.RIGHT_SHIFT)], left
    elif t == AssignmentOperationType.ASSIGN_ADDITION:
        return [Binary(left, left, right, BinaryType.ADDITION)], left
    elif t == AssignmentOperationType.ASSIGN_SUBTRACTION:
        return [Binary(left, left, right, BinaryType.SUBTRACTION)], left
    elif t == AssignmentOperationType.ASSIGN_MULTIPLICATION:
        return [Binary(left, left, right, BinaryType.MULTIPLICATION)], left
    elif t == AssignmentOperationType.ASSIGN_DIVISION:
        return [Binary(left, left, right, BinaryType.DIVISION)], left
    elif t == AssignmentOperationType.ASSIGN_MODULO:
        return [Binary(left, left, right, BinaryType.MODULO)], left

    raise SlithIRError("Missing type during assignment conversion")


class ExpressionToSlithIR(ExpressionVisitor):
    def __init__(self, expression: Expression, node: "Node"):
        from slither.core.cfg.node import NodeType

        self._expression = expression
        self._node = node
        self._result: List[Operation] = []
        self._visit_expression(self.expression)
        if node.type == NodeType.RETURN:
            r = Return(get(self.expression))
            r.set_expression(expression)
            self._result.append(r)
        for ir in self._result:
            ir.set_node(node)

    def result(self) -> List[Operation]:
        return self._result

    def _post_assignement_operation(self, expression):
        left = get(expression.expression_left)
        right = get(expression.expression_right)
        if isinstance(left, list):  # tuple expression:
            if isinstance(right, list):  # unbox assigment
                assert len(left) == len(right)
                for idx in range(len(left)):
                    if not left[idx] is None:
                        (operations, _) = convert_assignment(
                            left[idx],
                            right[idx],
                            expression.type,
                            expression.expression_return_type,
                        )
                        for operation in operations:
                            operation.set_expression(expression)
                            self._result.append(operation)
                set_val(expression, None)
            else:
                assert isinstance(right, TupleVariable)
                for idx in range(len(left)):
                    if not left[idx] is None:
                        operation = Unpack(left[idx], right, idx)
                        operation.set_expression(expression)
                        self._result.append(operation)
                set_val(expression, None)
        else:
            # Init of array, like
            # uint8[2] var = [1,2];
            if isinstance(right, list):
                operation = InitArray(right, left)
                operation.set_expression(expression)
                self._result.append(operation)
                set_val(expression, left)
            else:
                (operations, value_returned) = convert_assignment(
                    left, right, expression.type, expression.expression_return_type
                )
                for operation in operations:
                    operation.set_expression(expression)
                    self._result.append(operation)
                # Return left to handle
                # a = b = 1;
                set_val(expression, value_returned)

    def _post_binary_operation(self, expression):
        left = get(expression.expression_left)
        right = get(expression.expression_right)
        val = TemporaryVariable(self._node)

        operation = Binary(val, left, right, _binary_to_binary[expression.type])
        operation.set_expression(expression)
        self._result.append(operation)
        set_val(expression, val)

    def _post_call_expression(self, expression):
        called = get(expression.called)
        args = [get(a) for a in expression.arguments if a]
        for arg in args:
            arg_ = Argument(arg)
            arg_.set_expression(expression)
            self._result.append(arg_)
        if isinstance(called, Function):
            # internal call

            # If tuple
            if expression.type_call.startswith("tuple(") and expression.type_call != "tuple()":
                val = TupleVariable(self._node)
            else:
                val = TemporaryVariable(self._node)
            internal_call = InternalCall(called, len(args), val, expression.type_call)
            internal_call.set_expression(expression)
            self._result.append(internal_call)
            set_val(expression, val)
        else:
            # If tuple
            if expression.type_call.startswith("tuple(") and expression.type_call != "tuple()":
                val = TupleVariable(self._node)
            else:
                val = TemporaryVariable(self._node)

            message_call = TmpCall(called, len(args), val, expression.type_call)
            message_call.set_expression(expression)
            # Gas/value are only accessible here if the syntax {gas: , value: }
            # Is used over .gas().value()
            if expression.call_gas:
                call_gas = get(expression.call_gas)
                message_call.call_gas = call_gas
            if expression.call_value:
                call_value = get(expression.call_value)
                message_call.call_value = call_value
            self._result.append(message_call)
            set_val(expression, val)

    def _post_conditional_expression(self, expression):
        raise Exception("Ternary operator are not convertible to SlithIR {}".format(expression))

    def _post_elementary_type_name_expression(self, expression):
        set_val(expression, expression.type)

    def _post_identifier(self, expression):
        set_val(expression, expression.value)

    def _post_index_access(self, expression):
        left = get(expression.expression_left)
        right = get(expression.expression_right)
        # Left can be a type for abi.decode(var, uint[2])
        if isinstance(left, Type):
            # Nested type are not yet supported by abi.decode, so the assumption
            # Is that the right variable must be a constant
            assert isinstance(right, Constant)
            t = ArrayType(left, right.value)
            set_val(expression, t)
            return
        val = IndexVariable(self._node, left, right)
        # access to anonymous array
        # such as [0,1][x]
        if isinstance(left, list):
            init_array_val = TemporaryVariable(self._node)
            init_array_right = left
            left = init_array_val
            operation = InitArray(init_array_right, init_array_val)
            operation.set_expression(expression)
            self._result.append(operation)
        operation = Index(val, left, right, expression.type)
        operation.set_expression(expression)
        self._result.append(operation)
        set_val(expression, val)

    def _post_literal(self, expression):
        cst = Constant(expression.value, expression.type, expression.subdenomination)
        set_val(expression, cst)

    def _post_member_access(self, expression):
        expr = get(expression.expression)
        member_name = Constant(expression.member_name)
        # if str(member_name) in expr.context.get('MEMBERS', dict()):
        #     val = expr.context['MEMBERS'][str(member_name)]
        # else:
        val = MemberVariable(self._node, expr, member_name)
        #    expr.context['MEMBERS'][str(member_name)] = val
        member = AccessMember(expr, member_name, val)
        member.set_expression(expression)
        self._result.append(member)
        set_val(expression, val)

    def _post_new_array(self, expression):
        val = TemporaryVariable(self._node)
        operation = TmpNewArray(expression.depth, expression.array_type, val)
        operation.set_expression(expression)
        self._result.append(operation)
        set_val(expression, val)

    def _post_new_contract(self, expression):
        val = TemporaryVariable(self._node)
        operation = TmpNewContract(expression.contract_name, val)
        operation.set_expression(expression)
        self._result.append(operation)
        set_val(expression, val)

    def _post_new_elementary_type(self, expression):
        # TODO unclear if this is ever used?
        val = TemporaryVariable(self._node)
        operation = TmpNewElementaryType(expression.type, val)
        operation.set_expression(expression)
        self._result.append(operation)
        set_val(expression, val)

    def _post_tuple_expression(self, expression):
        expressions = [get(e) if e else None for e in expression.expressions]
        if len(expressions) == 1:
            val = expressions[0]
        else:
            val = expressions
        set_val(expression, val)

    def _post_type_conversion(self, expression):
        expr = get(expression.expression)
        val = TemporaryVariable(self._node)
        operation = TypeConversion(val, expr, expression.type)
        operation.set_expression(expression)
        self._result.append(operation)
        set_val(expression, val)

    def _post_unary_operation(self, expression):
        value = get(expression.expression)
        if expression.type in [UnaryOperationType.BANG, UnaryOperationType.TILD]:
            lvalue = TemporaryVariable(self._node)
            expression_type = (
                UnaryType.BANG if expression.type == UnaryOperationType.BANG else UnaryType.TILD
            )
            operation = Unary(lvalue, value, expression_type)
            operation.set_expression(expression)
            self._result.append(operation)
            set_val(expression, lvalue)
        elif expression.type in [UnaryOperationType.DELETE]:
            operation = Delete(value, value)
            operation.set_expression(expression)
            self._result.append(operation)
            set_val(expression, value)
        elif expression.type in [UnaryOperationType.PLUSPLUS_PRE]:
            operation = Binary(value, value, Constant("1", value.type), BinaryType.ADDITION)
            operation.set_expression(expression)
            self._result.append(operation)
            set_val(expression, value)
        elif expression.type in [UnaryOperationType.MINUSMINUS_PRE]:
            operation = Binary(value, value, Constant("1", value.type), BinaryType.SUBTRACTION)
            operation.set_expression(expression)
            self._result.append(operation)
            set_val(expression, value)
        elif expression.type in [UnaryOperationType.PLUSPLUS_POST]:
            lvalue = TemporaryVariable(self._node)
            operation = Assignment(lvalue, value, value.type)
            operation.set_expression(expression)
            self._result.append(operation)
            operation = Binary(value, value, Constant("1", value.type), BinaryType.ADDITION)
            operation.set_expression(expression)
            self._result.append(operation)
            set_val(expression, lvalue)
        elif expression.type in [UnaryOperationType.MINUSMINUS_POST]:
            lvalue = TemporaryVariable(self._node)
            operation = Assignment(lvalue, value, value.type)
            operation.set_expression(expression)
            self._result.append(operation)
            operation = Binary(value, value, Constant("1", value.type), BinaryType.SUBTRACTION)
            operation.set_expression(expression)
            self._result.append(operation)
            set_val(expression, lvalue)
        elif expression.type in [UnaryOperationType.PLUS_PRE]:
            set_val(expression, value)
        elif expression.type in [UnaryOperationType.MINUS_PRE]:
            lvalue = TemporaryVariable(self._node)
            operation = Binary(lvalue, Constant("0", value.type), value, BinaryType.SUBTRACTION)
            operation.set_expression(expression)
            self._result.append(operation)
            set_val(expression, lvalue)
        else:
            raise SlithIRError("Unary operation to IR not supported {}".format(expression))
