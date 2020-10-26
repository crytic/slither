import logging

from slither.core.declarations import (
    Function,
    SolidityVariable,
    SolidityVariableComposed,
    SolidityFunction,
)
from slither.core.expressions import (
    AssignmentOperationType,
    UnaryOperationType,
    BinaryOperationType,
    ElementaryTypeNameExpression,
    CallExpression,
    Identifier,
)
from slither.core.solidity_types import ArrayType, ElementaryType
from slither.core.solidity_types.type import Type
from slither.core.variables.local_variable_init_from_tuple import LocalVariableInitFromTuple
from slither.slithir.exceptions import SlithIRError
from slither.slithir.operations import (
    Assignment,
    Binary,
    BinaryType,
    Delete,
    Index,
    InitArray,
    InternalCall,
    Member,
    TypeConversion,
    Unary,
    Unpack,
    Return,
)
from slither.slithir.tmp_operations.argument import Argument
from slither.slithir.tmp_operations.tmp_call import TmpCall
from slither.slithir.tmp_operations.tmp_new_array import TmpNewArray
from slither.slithir.tmp_operations.tmp_new_contract import TmpNewContract
from slither.slithir.tmp_operations.tmp_new_elementary_type import TmpNewElementaryType
from slither.slithir.variables import (
    Constant,
    ReferenceVariable,
    TemporaryVariable,
    TupleVariable,
)
from slither.visitors.expression.expression import ExpressionVisitor

logger = logging.getLogger("VISTIOR:ExpressionToSlithIR")

key = "expressionToSlithIR"


def get(expression):
    val = expression.context[key]
    # we delete the item to reduce memory use
    del expression.context[key]
    return val


def set_val(expression, val):
    expression.context[key] = val


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

_signed_to_unsigned = {
    BinaryOperationType.DIVISION_SIGNED: BinaryType.DIVISION,
    BinaryOperationType.MODULO_SIGNED: BinaryType.MODULO,
    BinaryOperationType.LESS_SIGNED: BinaryType.LESS,
    BinaryOperationType.GREATER_SIGNED: BinaryType.GREATER,
    BinaryOperationType.RIGHT_SHIFT_ARITHMETIC: BinaryType.RIGHT_SHIFT,
}


def convert_assignment(left, right, t, return_type):
    if t == AssignmentOperationType.ASSIGN:
        return Assignment(left, right, return_type)
    if t == AssignmentOperationType.ASSIGN_OR:
        return Binary(left, left, right, BinaryType.OR)
    if t == AssignmentOperationType.ASSIGN_CARET:
        return Binary(left, left, right, BinaryType.CARET)
    if t == AssignmentOperationType.ASSIGN_AND:
        return Binary(left, left, right, BinaryType.AND)
    if t == AssignmentOperationType.ASSIGN_LEFT_SHIFT:
        return Binary(left, left, right, BinaryType.LEFT_SHIFT)
    if t == AssignmentOperationType.ASSIGN_RIGHT_SHIFT:
        return Binary(left, left, right, BinaryType.RIGHT_SHIFT)
    if t == AssignmentOperationType.ASSIGN_ADDITION:
        return Binary(left, left, right, BinaryType.ADDITION)
    if t == AssignmentOperationType.ASSIGN_SUBTRACTION:
        return Binary(left, left, right, BinaryType.SUBTRACTION)
    if t == AssignmentOperationType.ASSIGN_MULTIPLICATION:
        return Binary(left, left, right, BinaryType.MULTIPLICATION)
    if t == AssignmentOperationType.ASSIGN_DIVISION:
        return Binary(left, left, right, BinaryType.DIVISION)
    if t == AssignmentOperationType.ASSIGN_MODULO:
        return Binary(left, left, right, BinaryType.MODULO)

    raise SlithIRError("Missing type during assignment conversion")


class ExpressionToSlithIR(ExpressionVisitor):
    def __init__(self, expression, node):  # pylint: disable=super-init-not-called
        from slither.core.cfg.node import NodeType  # pylint: disable=import-outside-toplevel

        self._expression = expression
        self._node = node
        self._result = []
        self._visit_expression(self.expression)
        if node.type == NodeType.RETURN:
            r = Return(get(self.expression))
            r.set_expression(expression)
            self._result.append(r)
        for ir in self._result:
            ir.set_node(node)

    def result(self):
        return self._result

    def _post_assignement_operation(self, expression):
        left = get(expression.expression_left)
        right = get(expression.expression_right)
        if isinstance(left, list):  # tuple expression:
            if isinstance(right, list):  # unbox assigment
                assert len(left) == len(right)
                for idx, _ in enumerate(left):
                    if not left[idx] is None:
                        operation = convert_assignment(
                            left[idx],
                            right[idx],
                            expression.type,
                            expression.expression_return_type,
                        )
                        operation.set_expression(expression)
                        self._result.append(operation)
                set_val(expression, None)
            else:
                assert isinstance(right, TupleVariable)
                for idx, _ in enumerate(left):
                    if not left[idx] is None:
                        index = idx
                        # The following test is probably always true?
                        if (
                            isinstance(left[idx], LocalVariableInitFromTuple)
                            and left[idx].tuple_index is not None
                        ):
                            index = left[idx].tuple_index
                        operation = Unpack(left[idx], right, index)
                        operation.set_expression(expression)
                        self._result.append(operation)
                set_val(expression, None)
        # Tuple with only one element. We need to convert the assignment to a Unpack
        # Ex:
        # (uint a,,) = g()
        elif (
            isinstance(left, LocalVariableInitFromTuple)
            and left.tuple_index is not None
            and isinstance(right, TupleVariable)
        ):
            operation = Unpack(left, right, left.tuple_index)
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
                operation = convert_assignment(
                    left, right, expression.type, expression.expression_return_type
                )
                operation.set_expression(expression)
                self._result.append(operation)
                # Return left to handle
                # a = b = 1;
                set_val(expression, left)

    def _post_binary_operation(self, expression):
        left = get(expression.expression_left)
        right = get(expression.expression_right)
        val = TemporaryVariable(self._node)

        if expression.type in _signed_to_unsigned:
            new_left = TemporaryVariable(self._node)
            conv_left = TypeConversion(new_left, left, ElementaryType("int256"))
            conv_left.set_expression(expression)
            self._result.append(conv_left)

            if expression.type != BinaryOperationType.RIGHT_SHIFT_ARITHMETIC:
                new_right = TemporaryVariable(self._node)
                conv_right = TypeConversion(new_right, right, ElementaryType("int256"))
                conv_right.set_expression(expression)
                self._result.append(conv_right)
            else:
                new_right = right

            new_final = TemporaryVariable(self._node)
            operation = Binary(new_final, new_left, new_right, _signed_to_unsigned[expression.type])
            operation.set_expression(expression)
            self._result.append(operation)

            conv_final = TypeConversion(val, new_final, ElementaryType("uint256"))
            conv_final.set_expression(expression)
            self._result.append(conv_final)
        else:
            operation = Binary(val, left, right, _binary_to_binary[expression.type])
            operation.set_expression(expression)
            self._result.append(operation)

        set_val(expression, val)

    def _post_call_expression(
        self, expression
    ):  # pylint: disable=too-many-branches,too-many-statements
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
            # yul things
            if called.name == "caller()":
                val = TemporaryVariable(self._node)
                var = Assignment(val, SolidityVariableComposed("msg.sender"), "uint256")
                self._result.append(var)
                set_val(expression, val)
            elif called.name == "origin()":
                val = TemporaryVariable(self._node)
                var = Assignment(val, SolidityVariableComposed("tx.origin"), "uint256")
                self._result.append(var)
                set_val(expression, val)
            elif called.name == "extcodesize(uint256)":
                val = ReferenceVariable(self._node)
                var = Member(args[0], Constant("codesize"), val)
                self._result.append(var)
                set_val(expression, val)
            elif called.name == "selfbalance()":
                val = TemporaryVariable(self._node)
                var = TypeConversion(val, SolidityVariable("this"), ElementaryType("address"))
                self._result.append(var)

                val1 = ReferenceVariable(self._node)
                var1 = Member(val, Constant("balance"), val1)
                self._result.append(var1)
                set_val(expression, val1)
            elif called.name == "address()":
                val = TemporaryVariable(self._node)
                var = TypeConversion(val, SolidityVariable("this"), ElementaryType("address"))
                self._result.append(var)
                set_val(expression, val)
            elif called.name == "callvalue()":
                val = TemporaryVariable(self._node)
                var = Assignment(val, SolidityVariableComposed("msg.value"), "uint256")
                self._result.append(var)
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
                if expression.call_salt:
                    call_salt = get(expression.call_salt)
                    message_call.call_salt = call_salt
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
        val = ReferenceVariable(self._node)
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

        # Look for type(X).max / min
        # Because we looked at the AST structure, we need to look into the nested expression
        # Hopefully this is always on a direct sub field, and there is no weird construction
        if isinstance(expression.expression, CallExpression) and expression.member_name in [
            "min",
            "max",
        ]:
            if isinstance(expression.expression.called, Identifier):
                if expression.expression.called.value == SolidityFunction("type()"):
                    assert len(expression.expression.arguments) == 1
                    val = TemporaryVariable(self._node)
                    type_expression_found = expression.expression.arguments[0]
                    assert isinstance(type_expression_found, ElementaryTypeNameExpression)
                    type_found = type_expression_found.type
                    if expression.member_name == "min:":
                        op = Assignment(
                            val,
                            Constant(str(type_found.min), type_found),
                            type_found,
                        )
                    else:
                        op = Assignment(
                            val,
                            Constant(str(type_found.max), type_found),
                            type_found,
                        )
                    self._result.append(op)
                    set_val(expression, val)
                    return

        val = ReferenceVariable(self._node)
        member = Member(expr, Constant(expression.member_name), val)
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
        if expression.call_value:
            call_value = get(expression.call_value)
            operation.call_value = call_value
        if expression.call_salt:
            call_salt = get(expression.call_salt)
            operation.call_salt = call_salt

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

    def _post_unary_operation(
        self, expression
    ):  # pylint: disable=too-many-branches,too-many-statements
        value = get(expression.expression)
        if expression.type in [UnaryOperationType.BANG, UnaryOperationType.TILD]:
            lvalue = TemporaryVariable(self._node)
            operation = Unary(lvalue, value, expression.type)
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
