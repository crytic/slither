
from slither.core.declarations import Function, Structure
from slither.core.expressions import (AssignmentOperationType,
                                      UnaryOperationType)
from slither.core.solidity_types.array_type import ArrayType
from slither.slithir.operations import (Assignment, Binary, BinaryType, Delete,
                                        Index, InitArray, InternalCall, Member,
                                        TypeConversion, Unary, Unpack, NewContract,
                                        NewStructure, NewArray)
from slither.slithir.tmp_operations.argument import Argument
from slither.slithir.tmp_operations.tmp_call import TmpCall
from slither.slithir.tmp_operations.tmp_new_array import TmpNewArray
from slither.slithir.tmp_operations.tmp_new_contract import TmpNewContract
from slither.slithir.tmp_operations.tmp_new_elementary_type import \
    TmpNewElementaryType
from slither.slithir.tmp_operations.tmp_new_structure import TmpNewStructure
from slither.slithir.variables import (Constant, ReferenceVariable,
                                       TemporaryVariable, TupleVariable)
from slither.visitors.expression.expression import ExpressionVisitor

key = 'expressionToSlithIR'

def get(expression):
    val = expression.context[key]
    # we delete the item to reduce memory use
    del expression.context[key]
    return val

def set_val(expression, val):
    expression.context[key] = val

class ExpressionToSlithIR(ExpressionVisitor):

    def __init__(self, expression):
        self._expression = expression
        self._result = []
        self._visit_expression(self.expression)

    def result(self):
        return self._result

    def _post_assignement_operation(self, expression):
        left = get(expression.expression_left)
        right = get(expression.expression_right)
        if isinstance(left, list): # tuple expression:
            if isinstance(right, list): # unbox assigment
                assert len(left) == len(right)
                for idx in range(len(left)):
                    if not left[idx] is None:
                        operation = Assignment(left[idx], right[idx], expression.type, expression.expression_return_type)
                        self._result.append(operation)
                set_val(expression, None)
            else:
                assert isinstance(right, TupleVariable)
                for idx in range(len(left)):
                    if not left[idx] is None:
                        operation = Unpack(left[idx], right, idx)
                        self._result.append(operation)
                set_val(expression, None)
        else:
            # Init of array, like
            # uint8[2] var = [1,2];
            if isinstance(right, list):
                operation = InitArray(right, left)
                self._result.append(operation)
                set_val(expression, left)
            else:
                operation = Assignment(left, right, expression.type, expression.expression_return_type)
                self._result.append(operation)
                # Return left to handle
                # a = b = 1; 
                set_val(expression, left)

    def _post_binary_operation(self, expression):
        left = get(expression.expression_left)
        right = get(expression.expression_right)
        val = TemporaryVariable()

        operation = Binary(val, left, right, expression.type)
        self._result.append(operation)
        set_val(expression, val)

    def _post_call_expression(self, expression):
        called = get(expression.called)
        args = [get(a) for a in expression.arguments if a]
        for arg in args:
            arg_ = Argument(arg)
            self._result.append(arg_)
        if isinstance(called, Function):
            # internal call

            # If tuple
            if expression.type_call.startswith('tuple(') and expression.type_call != 'tuple()':
                val = TupleVariable()
            else:
                val = TemporaryVariable()
            internal_call = InternalCall(called, len(args), val, expression.type_call)
            self._result.append(internal_call)
            set_val(expression, val)
        else:
            val = TemporaryVariable()

            # If tuple
            if expression.type_call.startswith('tuple(') and expression.type_call != 'tuple()':
                val = TupleVariable()
            else:
                val = TemporaryVariable()

            message_call = TmpCall(called, len(args), val, expression.type_call)
            self._result.append(message_call)
            set_val(expression, val)

    def _post_conditional_expression(self, expression):
        raise Exception('Ternary operator are not convertible to SlithIR {}'.format(expression))

    def _post_elementary_type_name_expression(self, expression):
        set_val(expression, expression.type)

    def _post_identifier(self, expression):
        set_val(expression, expression.value)

    def _post_index_access(self, expression):
        left = get(expression.expression_left)
        right = get(expression.expression_right)
        val = ReferenceVariable()
        operation = Index(val, left, right, expression.type)
        self._result.append(operation)
        set_val(expression, val)

    def _post_literal(self, expression):
        set_val(expression, Constant(expression.value))

    def _post_member_access(self, expression):
        expr = get(expression.expression)
        val = ReferenceVariable()
        member = Member(expr, Constant(expression.member_name), val)
        self._result.append(member)
        set_val(expression, val)

    def _post_new_array(self, expression):
        val = TemporaryVariable()
        operation = TmpNewArray(expression.depth, expression.array_type, val)
        self._result.append(operation)
        set_val(expression, val)

    def _post_new_contract(self, expression):
        val = TemporaryVariable()
        operation = TmpNewContract(expression.contract_name, val)
        self._result.append(operation)
        set_val(expression, val)

    def _post_new_elementary_type(self, expression):
        # TODO unclear if this is ever used?
        val = TemporaryVariable()
        operation = TmpNewElementaryType(expression.type, val)
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
        val = TemporaryVariable()
        operation = TypeConversion(val, expr, expression.type)
        self._result.append(operation)
        set_val(expression, val)

    def _post_unary_operation(self, expression):
        value = get(expression.expression)
        if expression.type in [UnaryOperationType.BANG, UnaryOperationType.TILD]:
            lvalue = TemporaryVariable()
            operation = Unary(lvalue, value, expression.type)
            self._result.append(operation)
            set_val(expression, lvalue)
        elif expression.type in [UnaryOperationType.DELETE]:
            operation = Delete(value)
            self._result.append(operation)
            set_val(expression, value)
        elif expression.type in [UnaryOperationType.PLUSPLUS_PRE]:
            operation = Binary(value, value, Constant("1"), BinaryType.ADDITION)
            self._result.append(operation)
            set_val(expression, value)
        elif expression.type in [UnaryOperationType.MINUSMINUS_PRE]:
            operation = Binary(value, value, Constant("1"), BinaryType.SUBTRACTION)
            self._result.append(operation)
            set_val(expression, value)
        elif expression.type in [UnaryOperationType.PLUSPLUS_POST]:
            lvalue = TemporaryVariable()
            operation = Assignment(lvalue, value, AssignmentOperationType.ASSIGN, value.type)
            self._result.append(operation)
            operation = Binary(value, value, Constant("1"), BinaryType.ADDITION)
            self._result.append(operation)
            set_val(expression, lvalue)
        elif expression.type in [UnaryOperationType.MINUSMINUS_POST]:
            lvalue = TemporaryVariable()
            operation = Assignment(lvalue, value, AssignmentOperationType.ASSIGN, value.type)
            self._result.append(operation)
            operation = Binary(value, value, Constant("1"), BinaryType.SUBTRACTION)
            self._result.append(operation)
            set_val(expression, lvalue)
        elif expression.type in [UnaryOperationType.PLUS_PRE]:
            set_val(expression, value)
        elif expression.type in [UnaryOperationType.MINUS_PRE]:
            lvalue = TemporaryVariable()
            operation = Binary(lvalue, Constant("0"), value, BinaryType.SUBTRACTION)
            self._result.append(operation)
            set_val(expression, lvalue)
        else:
            raise Exception('Unary operation to IR not supported {}'.format(expression))

