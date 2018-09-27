
from slither.visitors.expression.expression import ExpressionVisitor

from slither.core.expressions.assignment_operation import AssignmentOperationType
from slither.core.declarations.function import Function
from slither.core.declarations.structure import Structure
from slither.core.expressions.unary_operation import UnaryOperationType
from slither.core.solidity_types.array_type import ArrayType

from slither.slithir.operations.assignment import Assignment
from slither.slithir.operations.binary import BinaryOperation, BinaryOperationType
from slither.slithir.operations.unary import UnaryOperation
from slither.slithir.operations.index import Index
from slither.slithir.operations.internal_call import InternalCall
from slither.slithir.operations.member import Member
from slither.slithir.operations.type_conversion import TypeConversion
from slither.slithir.operations.delete import Delete
from slither.slithir.operations.unpack import Unpack
from slither.slithir.operations.init_array import InitArray

from slither.slithir.tmp_operations.tmp_call import TmpCall
from slither.slithir.tmp_operations.tmp_new_elementary_type import TmpNewElementaryType
from slither.slithir.tmp_operations.tmp_new_contract import TmpNewContract
from slither.slithir.tmp_operations.tmp_new_array import TmpNewArray
from slither.slithir.tmp_operations.tmp_new_structure import TmpNewStructure
from slither.slithir.tmp_operations.argument import Argument

from slither.slithir.variables.temporary import TemporaryVariable
from slither.slithir.variables.tuple import TupleVariable
from slither.slithir.variables.constant import Constant
from slither.slithir.variables.reference import ReferenceVariable

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

        operation = BinaryOperation(val, left, right, expression.type)
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

            if isinstance(called, Structure) and False:
                operation = TmpNewStructure(called, val)
#                self._result.append(message_call)
#                set_val(expression, val)
            else:
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
            operation = UnaryOperation(lvalue, value, expression.type)
            self._result.append(operation)
            set_val(expression, lvalue)
        elif expression.type in [UnaryOperationType.DELETE]:
            operation = Delete(value)
            self._result.append(operation)
            set_val(expression, value)
        elif expression.type in [UnaryOperationType.PLUSPLUS_PRE]:
            operation = BinaryOperation(value, value, Constant("1"), BinaryOperationType.ADDITION)
            self._result.append(operation)
            set_val(expression, value)
        elif expression.type in [UnaryOperationType.MINUSMINUS_PRE]:
            operation = BinaryOperation(value, value, Constant("1"), BinaryOperationType.SUBTRACTION)
            self._result.append(operation)
            set_val(expression, value)
        elif expression.type in [UnaryOperationType.PLUSPLUS_POST]:
            lvalue = TemporaryVariable()
            operation = Assignment(lvalue, value, AssignmentOperationType.ASSIGN, value.type)
            self._result.append(operation)
            operation = BinaryOperation(value, value, Constant("1"), BinaryOperationType.ADDITION)
            self._result.append(operation)
            set_val(expression, lvalue)
        elif expression.type in [UnaryOperationType.MINUSMINUS_POST]:
            lvalue = TemporaryVariable()
            operation = Assignment(lvalue, value, AssignmentOperationType.ASSIGN, value.type)
            self._result.append(operation)
            operation = BinaryOperation(value, value, Constant("1"), BinaryOperationType.SUBTRACTION)
            self._result.append(operation)
            set_val(expression, lvalue)
        elif expression.type in [UnaryOperationType.PLUS_PRE]:
            set_val(expression, value)
        elif expression.type in [UnaryOperationType.MINUS_PRE]:
            set_val(expression, Constant("-"+str(value.value)))
        else:
            raise Exception('Unary operation to IR not supported {}'.format(expression))


