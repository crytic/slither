import logging
from typing import Union, List, TYPE_CHECKING, Any

from slither.core import expressions
from slither.core.scope.scope import FileScope
from slither.core.declarations import (
    Function,
    SolidityVariable,
    SolidityVariableComposed,
    SolidityFunction,
    Contract,
    EnumContract,
    EnumTopLevel,
    Enum,
    SolidityImportPlaceHolder,
    Import,
    Structure,
)
from slither.core.expressions import (
    AssignmentOperation,
    AssignmentOperationType,
    UnaryOperationType,
    BinaryOperationType,
    ElementaryTypeNameExpression,
    CallExpression,
    Identifier,
    MemberAccess,
    ConditionalExpression,
    NewElementaryType,
)
from slither.core.expressions.binary_operation import BinaryOperation
from slither.core.expressions.expression import Expression
from slither.core.expressions.index_access import IndexAccess
from slither.core.expressions.literal import Literal
from slither.core.expressions.new_array import NewArray
from slither.core.expressions.new_contract import NewContract
from slither.core.expressions.tuple_expression import TupleExpression
from slither.core.expressions.unary_operation import UnaryOperation
from slither.core.solidity_types import ArrayType, ElementaryType, TypeAlias, UserDefinedType
from slither.core.solidity_types.type import Type
from slither.core.variables.local_variable import LocalVariable
from slither.core.variables.local_variable_init_from_tuple import LocalVariableInitFromTuple
from slither.core.variables.state_variable import StateVariable
from slither.core.variables.variable import Variable
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
    UnaryType,
    Unpack,
    Return,
    SolidityCall,
    Operation,
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

if TYPE_CHECKING:
    from slither.core.cfg.node import Node

logger = logging.getLogger("VISTIOR:ExpressionToSlithIR")

key = "expressionToSlithIR"


def get(expression: Expression) -> Any:
    val = expression.context[key]
    # we delete the item to reduce memory use
    del expression.context[key]
    return val


def set_val(expression: Expression, val: Any) -> None:
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


_unary_to_unary = {
    UnaryOperationType.BANG: UnaryType.BANG,
    UnaryOperationType.TILD: UnaryType.TILD,
}


_signed_to_unsigned = {
    BinaryOperationType.DIVISION_SIGNED: BinaryType.DIVISION,
    BinaryOperationType.MODULO_SIGNED: BinaryType.MODULO,
    BinaryOperationType.LESS_SIGNED: BinaryType.LESS,
    BinaryOperationType.GREATER_SIGNED: BinaryType.GREATER,
    BinaryOperationType.RIGHT_SHIFT_ARITHMETIC: BinaryType.RIGHT_SHIFT,
}


def convert_assignment(
    left: Union[LocalVariable, StateVariable, ReferenceVariable],
    right: Union[LocalVariable, StateVariable, ReferenceVariable],
    t: AssignmentOperationType,
    return_type: Type,
) -> Union[Binary, Assignment]:
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

    # pylint: disable=super-init-not-called
    def __init__(self, expression: Expression, node: "Node") -> None:
        from slither.core.cfg.node import NodeType  # pylint: disable=import-outside-toplevel

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

    # pylint: disable=too-many-branches,too-many-statements
    def _post_assignement_operation(self, expression: AssignmentOperation) -> None:
        left = get(expression.expression_left)
        right = get(expression.expression_right)
        operation: Operation
        if isinstance(left, list):  # tuple expression:
            if isinstance(right, list):  # unbox assigment
                assert len(left) == len(right)
                for idx, _ in enumerate(left):
                    if (
                        not left[idx] is None
                        and expression.type
                        and expression.expression_return_type
                    ):
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
            elif isinstance(left.type, ArrayType):
                # Special case for init of array, when the right has only one element
                operation = InitArray([right], left)
                operation.set_expression(expression)
                self._result.append(operation)
                set_val(expression, left)

            elif (
                isinstance(left.type, UserDefinedType)
                and isinstance(left.type.type, Structure)
                and isinstance(right, TupleVariable)
            ):
                # This will result in a `NewStructure` operation where
                # each field is assigned the value unpacked from the tuple
                # (see `slither.vyper_parsing.type_parsing.parse_type`)
                args = []
                for idx, elem in enumerate(left.type.type.elems.values()):
                    temp = TemporaryVariable(self._node)
                    temp.type = elem.type
                    args.append(temp)
                    operation = Unpack(temp, right, idx)
                    operation.set_expression(expression)
                    self._result.append(operation)

                for arg in args:
                    op = Argument(arg)
                    op.set_expression(expression)
                    self._result.append(op)

                operation = TmpCall(
                    left.type.type, len(left.type.type.elems), left, left.type.type.name
                )
                operation.set_expression(expression)
                self._result.append(operation)

            else:
                operation = convert_assignment(
                    left, right, expression.type, expression.expression_return_type
                )
                operation.set_expression(expression)
                self._result.append(operation)
                # Return left to handle
                # a = b = 1;
                set_val(expression, left)

    def _post_binary_operation(self, expression: BinaryOperation) -> None:
        left = get(expression.expression_left)
        right = get(expression.expression_right)
        val = TemporaryVariable(self._node)

        if expression.type in _signed_to_unsigned:
            new_left = TemporaryVariable(self._node)
            conv_left = TypeConversion(new_left, left, ElementaryType("int256"))
            new_left.set_type(ElementaryType("int256"))
            conv_left.set_expression(expression)
            self._result.append(conv_left)

            if expression.type != BinaryOperationType.RIGHT_SHIFT_ARITHMETIC:
                new_right = TemporaryVariable(self._node)
                conv_right = TypeConversion(new_right, right, ElementaryType("int256"))
                new_right.set_type(ElementaryType("int256"))
                conv_right.set_expression(expression)
                self._result.append(conv_right)
            else:
                new_right = right

            new_final = TemporaryVariable(self._node)
            operation = Binary(new_final, new_left, new_right, _signed_to_unsigned[expression.type])
            operation.set_expression(expression)
            self._result.append(operation)

            conv_final = TypeConversion(val, new_final, ElementaryType("uint256"))
            val.set_type(ElementaryType("uint256"))
            conv_final.set_expression(expression)
            self._result.append(conv_final)
        else:
            operation = Binary(val, left, right, _binary_to_binary[expression.type])
            operation.set_expression(expression)
            self._result.append(operation)

        set_val(expression, val)

    # pylint: disable=too-many-branches,too-many-statements,too-many-locals
    def _post_call_expression(self, expression: CallExpression) -> None:

        assert isinstance(expression, CallExpression)

        expression_called = expression.called
        called = get(expression_called)

        args = [get(a) for a in expression.arguments if a]
        val: Union[TupleVariable, TemporaryVariable]
        var: Operation
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
            internal_call = InternalCall(
                called, len(args), val, expression.type_call, names=expression.names
            )
            internal_call.set_expression(expression)
            self._result.append(internal_call)
            set_val(expression, val)

        # User defined types
        elif (
            isinstance(called, TypeAlias)
            and isinstance(expression_called, MemberAccess)
            and expression_called.member_name in ["wrap", "unwrap"]
            and len(args) == 1
        ):
            # wrap: underlying_type -> alias
            # unwrap: alias -> underlying_type
            dest_type: Union[TypeAlias, ElementaryType] = (
                called if expression_called.member_name == "wrap" else called.underlying_type
            )
            val = TemporaryVariable(self._node)
            var = TypeConversion(val, args[0], dest_type)
            var.set_expression(expression)
            val.set_type(dest_type)
            self._result.append(var)
            set_val(expression, val)

        # yul things
        elif called.name == "caller()":
            val = TemporaryVariable(self._node)
            var = Assignment(val, SolidityVariableComposed("msg.sender"), ElementaryType("uint256"))
            self._result.append(var)
            set_val(expression, val)
        elif called.name == "origin()":
            val = TemporaryVariable(self._node)
            var = Assignment(val, SolidityVariableComposed("tx.origin"), ElementaryType("uint256"))
            self._result.append(var)
            set_val(expression, val)
        elif called.name == "extcodesize(uint256)":
            val_ref = ReferenceVariable(self._node)
            var = Member(args[0], Constant("codesize"), val_ref)
            self._result.append(var)
            set_val(expression, val_ref)
        elif called.name == "selfbalance()":
            val = TemporaryVariable(self._node)
            var = TypeConversion(val, SolidityVariable("this"), ElementaryType("address"))
            val.set_type(ElementaryType("address"))
            self._result.append(var)

            val1 = ReferenceVariable(self._node)
            var1 = Member(val, Constant("balance"), val1)
            self._result.append(var1)
            set_val(expression, val1)
        elif called.name == "address()":
            val = TemporaryVariable(self._node)
            var = TypeConversion(val, SolidityVariable("this"), ElementaryType("address"))
            val.set_type(ElementaryType("address"))
            self._result.append(var)
            set_val(expression, val)
        elif called.name == "callvalue()":
            val = TemporaryVariable(self._node)
            var = Assignment(val, SolidityVariableComposed("msg.value"), ElementaryType("uint256"))
            self._result.append(var)
            set_val(expression, val)

        else:
            # If tuple
            if expression.type_call.startswith("tuple(") and expression.type_call != "tuple()":
                val = TupleVariable(self._node)
            else:
                val = TemporaryVariable(self._node)

            message_call = TmpCall(
                called, len(args), val, expression.type_call, names=expression.names
            )
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

    def _post_conditional_expression(self, expression: ConditionalExpression) -> None:
        raise Exception(f"Ternary operator are not convertible to SlithIR {expression}")

    def _post_elementary_type_name_expression(
        self,
        expression: ElementaryTypeNameExpression,
    ) -> None:
        set_val(expression, expression.type)

    def _post_identifier(self, expression: Identifier) -> None:
        set_val(expression, expression.value)

    def _post_index_access(self, expression: IndexAccess) -> None:
        left = get(expression.expression_left)
        right = get(expression.expression_right)
        operation: Operation
        # Left can be a type for abi.decode(var, uint[2])
        if isinstance(left, (Type, Contract, Enum)):
            # Nested type are not yet supported by abi.decode, so the assumption
            # Is that the right variable must be a constant
            assert isinstance(right, Constant)
            # Case for abi.decode(var, I[2]) where I is an interface/contract or an enum
            if isinstance(left, (Contract, Enum)):
                left = UserDefinedType(left)
            t = ArrayType(left, int(right.value))
            set_val(expression, t)
            return
        val = ReferenceVariable(self._node)

        if (
            isinstance(left, LocalVariable)
            and isinstance(left.type, UserDefinedType)
            and isinstance(left.type.type, Structure)
        ):
            # We rewrite the index access to a tuple variable as
            # an access to its field i.e. the 0th element is the field "_0"
            # (see `slither.vyper_parsing.type_parsing.parse_type`)
            operation = Member(left, Constant("_" + str(right)), val)
            operation.set_expression(expression)
            self._result.append(operation)
            set_val(expression, val)
            return

        # access to anonymous array
        # such as [0,1][x]
        if isinstance(left, list):
            init_array_val = TemporaryVariable(self._node)
            init_array_right = left
            left = init_array_val
            operation = InitArray(init_array_right, init_array_val)
            operation.set_expression(expression)
            self._result.append(operation)

        operation = Index(val, left, right)
        operation.set_expression(expression)
        self._result.append(operation)
        set_val(expression, val)

    def _post_literal(self, expression: Literal) -> None:
        expression_type = expression.type
        assert isinstance(expression_type, ElementaryType)
        cst = Constant(expression.value, expression_type, expression.subdenomination)
        set_val(expression, cst)

    def _post_member_access(self, expression: MemberAccess) -> None:
        expr = get(expression.expression)

        # Look for type(X).max / min
        # Because we looked at the AST structure, we need to look into the nested expression
        # Hopefully this is always on a direct sub field, and there is no weird construction
        # pylint: disable=too-many-nested-blocks
        if isinstance(expression.expression, CallExpression) and expression.member_name in [
            "min",
            "max",
        ]:
            if isinstance(expression.expression.called, Identifier):
                if expression.expression.called.value == SolidityFunction("type()"):
                    assert len(expression.expression.arguments) == 1
                    val = TemporaryVariable(self._node)
                    type_expression_found = expression.expression.arguments[0]
                    type_found: Union[ElementaryType, UserDefinedType]
                    if isinstance(type_expression_found, ElementaryTypeNameExpression):
                        type_expression_found_type = type_expression_found.type
                        assert isinstance(type_expression_found_type, ElementaryType)
                        type_found = type_expression_found_type
                        min_value = type_found.min
                        max_value = type_found.max
                        constant_type = type_found
                    else:
                        # type(enum).max/min
                        # Case when enum is in another contract e.g. type(C.E).max
                        if isinstance(type_expression_found, MemberAccess):
                            contract = type_expression_found.expression.value
                            assert isinstance(contract, Contract)
                            for enum in contract.enums:
                                if enum.name == type_expression_found.member_name:
                                    type_found_in_expression = enum
                                    type_found = UserDefinedType(enum)
                                    break
                        else:
                            assert isinstance(type_expression_found, Identifier)
                            type_found_in_expression = type_expression_found.value
                            assert isinstance(
                                type_found_in_expression, (EnumContract, EnumTopLevel)
                            )
                            type_found = UserDefinedType(type_found_in_expression)
                        constant_type = None
                        min_value = type_found_in_expression.min
                        max_value = type_found_in_expression.max
                    if expression.member_name == "min":
                        op = Assignment(
                            val,
                            Constant(str(min_value), constant_type),
                            type_found,
                        )
                    else:
                        op = Assignment(
                            val,
                            Constant(str(max_value), constant_type),
                            type_found,
                        )
                    self._result.append(op)
                    set_val(expression, val)
                    return

        # This does not support solidity 0.4 contract_name.balance
        if (
            isinstance(expr, Variable)
            and expr.type == ElementaryType("address")
            and expression.member_name in ["balance", "code", "codehash"]
        ):
            val = TemporaryVariable(self._node)
            name = expression.member_name + "(address)"
            sol_func = SolidityFunction(name)
            s = SolidityCall(
                sol_func,
                1,
                val,
                sol_func.return_type,
            )
            s.set_expression(expression)
            s.arguments.append(expr)
            self._result.append(s)
            set_val(expression, val)
            return

        if isinstance(expr, TypeAlias) and expression.member_name in ["wrap", "unwrap"]:
            # The logic is be handled by _post_call_expression
            set_val(expression, expr)
            return

        if isinstance(expr, Contract):
            # Early lookup to detect user defined types from other contracts definitions
            # contract A { type MyInt is int}
            # contract B { function f() public{ A.MyInt test = A.MyInt.wrap(1);}}
            # The logic is handled by _post_call_expression
            if expression.member_name in expr.file_scope.type_aliases:
                set_val(expression, expr.file_scope.type_aliases[expression.member_name])
                return
            # Lookup errors referred to as member of contract e.g. Test.myError.selector
            if expression.member_name in expr.custom_errors_as_dict:
                set_val(expression, expr.custom_errors_as_dict[expression.member_name])
                return
            # Lookup enums when in a different contract e.g. C.E
            if str(expression) in expr.enums_as_dict:
                set_val(expression, expr.enums_as_dict[str(expression)])
                return

        if isinstance(expr, (SolidityImportPlaceHolder, Import)):
            scope = (
                expr.import_directive.scope
                if isinstance(expr, SolidityImportPlaceHolder)
                else expr.scope
            )
            if self._check_elem_in_scope(expression.member_name, scope, expression):
                return

        val_ref = ReferenceVariable(self._node)
        member = Member(expr, Constant(expression.member_name), val_ref)
        member.set_expression(expression)
        self._result.append(member)
        set_val(expression, val_ref)

    def _check_elem_in_scope(self, elem: str, scope: FileScope, expression: MemberAccess) -> bool:
        if elem in scope.renaming:
            self._check_elem_in_scope(scope.renaming[elem], scope, expression)
            return True

        if elem in scope.contracts:
            set_val(expression, scope.contracts[elem])
            return True

        if elem in scope.structures:
            set_val(expression, scope.structures[elem])
            return True

        if elem in scope.variables:
            set_val(expression, scope.variables[elem])
            return True

        if elem in scope.enums:
            set_val(expression, scope.enums[elem])
            return True

        if elem in scope.type_aliases:
            set_val(expression, scope.type_aliases[elem])
            return True

        for import_directive in scope.imports:
            if elem == import_directive.alias:
                set_val(expression, import_directive)
                return True

        for custom_error in scope.custom_errors:
            if custom_error.name == elem:
                set_val(expression, custom_error)
                return True

        if str(expression.type).startswith("function "):
            # This is needed to handle functions overloading
            signature_to_seaarch = (
                str(expression.type)
                .replace("function ", elem)
                .replace("pure ", "")
                .replace("view ", "")
                .replace("struct ", "")
                .replace("enum ", "")
                .replace(" memory", "")
                .split(" returns", maxsplit=1)[0]
            )

            for function in scope.functions:
                if signature_to_seaarch == function.full_name:
                    set_val(expression, function)
                    return True

        return False

    def _post_new_array(self, expression: NewArray) -> None:
        val = TemporaryVariable(self._node)
        operation = TmpNewArray(expression.array_type, val)
        operation.set_expression(expression)
        self._result.append(operation)
        set_val(expression, val)

    def _post_new_contract(self, expression: NewContract) -> None:
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

    def _post_new_elementary_type(self, expression: NewElementaryType) -> None:
        # TODO unclear if this is ever used?
        val = TemporaryVariable(self._node)
        operation = TmpNewElementaryType(expression.type, val)
        operation.set_expression(expression)
        self._result.append(operation)
        set_val(expression, val)

    def _post_tuple_expression(self, expression: TupleExpression) -> None:
        all_expressions = [get(e) if e else None for e in expression.expressions]
        if len(all_expressions) == 1:
            val = all_expressions[0]
        else:
            val = all_expressions
        set_val(expression, val)

    def _post_type_conversion(self, expression: expressions.TypeConversion) -> None:
        assert expression.expression
        expr = get(expression.expression)
        val = TemporaryVariable(self._node)
        expression_type = expression.type
        assert isinstance(expression_type, (TypeAlias, UserDefinedType, ElementaryType, ArrayType))
        operation = TypeConversion(val, expr, expression_type)
        val.set_type(expression.type)
        operation.set_expression(expression)
        self._result.append(operation)
        set_val(expression, val)

    # pylint: disable=too-many-statements
    def _post_unary_operation(self, expression: UnaryOperation) -> None:
        value = get(expression.expression)
        operation: Operation
        if expression.type in [UnaryOperationType.BANG, UnaryOperationType.TILD]:
            lvalue = TemporaryVariable(self._node)
            operation = Unary(lvalue, value, _unary_to_unary[expression.type])
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
            raise SlithIRError(f"Unary operation to IR not supported {expression}")
