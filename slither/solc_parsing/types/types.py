from typing import List, Optional, Dict, Union


class ASTNode:
    __slots__ = "src", "id"

    def __init__(self, src: str, id: int):
        self.src = src
        self.id = id


class SourceUnit(ASTNode):
    __slots__ = "nodes"

    def __init__(self, nodes: List[ASTNode], **kwargs):
        super().__init__(**kwargs)
        self.nodes = nodes


class Declaration(ASTNode):
    __slots__ = "name", "canonical_name", "visibility"

    def __init__(self, name: str, canonical_name: Optional[str], visibility: Optional[str], **kwargs):
        super().__init__(**kwargs)
        self.name = name
        self.canonical_name = canonical_name
        self.visibility = visibility


class PragmaDirective(ASTNode):
    __slots__ = "literals"

    def __init__(self, literals: List[str], **kwargs):
        super().__init__(**kwargs)
        self.literals = literals


class ImportDirective(Declaration):
    __slots__ = "path"

    def __init__(self, path: str, **kwargs):
        super().__init__(**kwargs)
        self.path = path


# kind can be: "interface", "contract", "library"
class ContractDefinition(Declaration):
    __slots__ = "kind", "linearized_base_contracts", "base_contracts", "nodes"

    def __init__(self, kind: Optional[str], base: Optional[List[int]], base_contracts: List['InheritanceSpecifier'],
                 nodes: List[ASTNode], **kwargs):
        super().__init__(**kwargs)
        self.kind = kind
        self.linearized_base_contracts = base
        self.base_contracts = base_contracts
        self.nodes = nodes


class InheritanceSpecifier(ASTNode):
    __slots__ = "basename", "args"

    def __init__(self, basename: 'UserDefinedTypeName', args: Optional[List['Expression']], **kwargs):
        super().__init__(**kwargs)
        self.basename = basename
        self.args = args


class UsingForDirective(ASTNode):
    __slots__ = "library", "typename"

    def __init__(self, library: 'UserDefinedTypeName', typename: 'TypeName', **kwargs):
        super().__init__(**kwargs)
        self.library = library
        self.typename = typename


class StructDefinition(Declaration):
    __slots__ = "members"

    def __init__(self, members: List['VariableDeclaration'], **kwargs):
        super().__init__(**kwargs)
        self.members = members


class EnumDefinition(Declaration):
    __slots__ = "members"

    def __init__(self, members: List['EnumValue'], **kwargs):
        super().__init__(**kwargs)
        self.members = members


class EnumValue(Declaration):
    pass


class ParameterList(ASTNode):
    __slots__ = "params"

    def __init__(self, params: List['VariableDeclaration'], **kwargs):
        super().__init__(**kwargs)
        self.params = params


class CallableDeclaration(Declaration):
    __slots__ = "params", "rets"

    def __init__(self, params: ParameterList, rets: Optional[ParameterList], **kwargs):
        super().__init__(**kwargs)
        self.params = params
        self.rets = rets


# mutability can be: "pure", "view", "nonpayable", "payable"
# kind can be: "function", "constructor", "fallback", "receive"
class FunctionDefinition(CallableDeclaration):
    __slots__ = "mutability", "kind", "modifiers", "body"

    def __init__(self, mutability: str, kind: str, modifiers: List['ModifierInvocation'], body: 'Block', **kwargs):
        super().__init__(**kwargs)
        self.mutability = mutability
        self.kind = kind
        self.modifiers = modifiers
        self.body = body


class VariableDeclaration(Declaration):
    __slots__ = "typename", "value", "type_str", "constant", "indexed", "location"

    def __init__(self, typename: 'TypeName', value: Optional['Expression'], type_str: str, constant: bool,
                 indexed: Optional[bool], location: str, **kwargs):
        super().__init__(**kwargs)
        self.type_str = type_str
        self.value = value
        self.constant = constant
        self.typename = typename
        self.indexed = indexed
        self.location = location


class ModifierDefinition(CallableDeclaration):
    __slots__ = "body"

    def __init__(self, body: 'Block', **kwargs):
        super().__init__(**kwargs)
        self.body = body


class ModifierInvocation(ASTNode):
    __slots__ = "modifier", "args"

    def __init__(self, modifier: 'Identifier', args: Optional[List['Expression']], **kwargs):
        super().__init__(**kwargs)
        self.modifier = modifier
        self.args = args


class EventDefinition(CallableDeclaration):
    __slots__ = "anonymous"

    def __init__(self, anonymous: bool, **kwargs):
        super().__init__(**kwargs)
        self.anonymous = anonymous


class TypeName(ASTNode):
    pass


class ElementaryTypeName(TypeName):
    __slots__ = "name", "mutability"

    def __init__(self, name: str, mutability: Optional[str], **kwargs):
        super().__init__(**kwargs)
        self.name = name
        self.mutability = mutability


class UserDefinedTypeName(TypeName):
    """
    referenced_declaration might be None for old versions of solidity
    """
    __slots__ = "name", "referenced_declaration"

    def __init__(self, name: str, referenced_declaration: Optional[int], **kwargs):
        super().__init__(**kwargs)
        self.name = name
        self.referenced_declaration = referenced_declaration


class FunctionTypeName(TypeName):
    __slots__ = "params", "rets", "visibility", "mutability"

    def __init__(self, params: 'ParameterList', rets: 'ParameterList', visibility: str, mutability: str, **kwargs):
        super().__init__(**kwargs)
        self.params = params
        self.rets = rets
        self.visibility = visibility
        self.mutability = mutability


class Mapping(TypeName):
    __slots__ = "key", "value"

    def __init__(self, key: TypeName, value: TypeName, **kwargs):
        super().__init__(**kwargs)
        self.key = key
        self.value = value


class ArrayTypeName(TypeName):
    __slots__ = "base", "len"

    def __init__(self, base: TypeName, len: Optional['Expression'], **kwargs):
        super().__init__(**kwargs)
        self.base = base
        self.len = len


class Statement(ASTNode):
    pass


class InlineAssembly(Statement):
    __slots__ = "ast"

    def __init__(self, ast: Union[Dict, str], **kwargs):
        super().__init__(**kwargs)
        self.ast = ast


class Block(Statement):
    __slots__ = "statements"

    def __init__(self, statements: List[Statement], **kwargs):
        super().__init__(**kwargs)
        self.statements = statements


class PlaceholderStatement(Statement):
    pass


class IfStatement(Statement):
    __slots__ = "condition", "true_body", "false_body"

    def __init__(self, condition: 'Expression', true_budy: Statement, false_body: Optional[Statement], **kwargs):
        super().__init__(**kwargs)
        self.condition = condition
        self.true_body = true_budy
        self.false_body = false_body


class TryCatchClause(ASTNode):
    __slots__ = "error_name", "params", "block"

    def __init__(self, error_name: str, params: Optional['ParameterList'], block: Block, **kwargs):
        super().__init__(**kwargs)
        self.error_name = error_name
        self.params = params
        self.block = block


class TryStatement(Statement):
    __slots__ = "external_call", "clauses"

    def __init__(self, external_call: 'Expression', clauses: List[TryCatchClause], **kwargs):
        super().__init__(**kwargs)
        self.external_call = external_call
        self.clauses = clauses


class WhileStatement(Statement):
    __slots__ = "condition", "body", "is_do_while"

    def __init__(self, condition: 'Expression', body: Statement, is_do_while: bool, **kwargs):
        super().__init__(**kwargs)
        self.condition = condition
        self.body = body
        self.is_do_while = is_do_while


class ForStatement(Statement):
    __slots__ = "init", "cond", "loop", "body"

    def __init__(self, init: Optional[Statement], cond: Optional['Expression'], loop: Optional['ExpressionStatement'],
                 body: Statement, **kwargs):
        super().__init__(**kwargs)
        self.init = init
        self.cond = cond
        self.loop = loop
        self.body = body


class Continue(Statement):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)


class Break(Statement):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)


class Return(Statement):
    __slots__ = "expression"

    def __init__(self, expression: Optional['Expression'], **kwargs):
        super().__init__(**kwargs)
        self.expression = expression


class Throw(Statement):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)


class EmitStatement(Statement):
    __slots__ = "event_call"

    def __init__(self, event_call: 'FunctionCall', **kwargs):
        super().__init__(**kwargs)
        self.event_call = event_call


class VariableDeclarationStatement(Statement):
    __slots__ = "variables", "initial_value"

    def __init__(self, variables: List[Optional['VariableDeclaration']], initial_value: Optional['Expression'],
                 **kwargs):
        super().__init__(**kwargs)
        self.variables = variables
        self.initial_value = initial_value


class ExpressionStatement(Statement):
    __slots__ = "expression"

    def __init__(self, expression: 'Expression', **kwargs):
        super().__init__(**kwargs)
        self.expression = expression


class Expression(ASTNode):
    __slots__ = "type_str", "constant", "pure"

    def __init__(self, type_str: str, constant: bool, pure: bool, **kwargs):
        super().__init__(**kwargs)
        self.type_str = type_str
        self.constant = constant
        self.pure = pure


class Conditional(Expression):
    __slots__ = "condition", "true_expr", "false_expr"

    def __init__(self, condition: Expression, true_expr: Expression, false_expr: Expression, **kwargs):
        super().__init__(**kwargs)
        self.condition = condition
        self.true_expr = true_expr
        self.false_expr = false_expr


class Assignment(Expression):
    __slots__ = "left", "operator", "right"

    def __init__(self, left: Expression, operator: str, right: Expression, **kwargs):
        super().__init__(**kwargs)
        self.left = left
        self.operator = operator
        self.right = right


class TupleExpression(Expression):
    __slots__ = "components", "is_array"

    def __init__(self, components: List[Optional[Expression]], is_array: bool, **kwargs):
        super().__init__(**kwargs)

        self.components = components
        self.is_array = is_array


class UnaryOperation(Expression):
    __slots__ = "operator", "expression", "is_prefix"

    def __init__(self, operator: str, expression: Expression, is_prefix: bool, **kwargs):
        super().__init__(**kwargs)
        self.operator = operator
        self.expression = expression
        self.is_prefix = is_prefix


class BinaryOperation(Expression):
    __slots__ = "left", "operator", "right"

    def __init__(self, left: Expression, operator: str, right: Expression, **kwargs):
        super().__init__(**kwargs)
        self.left = left
        self.operator = operator
        self.right = right


# kind can be: "functionCall", "typeConversion", "structConstructorCall"
class FunctionCall(Expression):
    __slots__ = "kind", "expression", "arguments", "names"

    def __init__(self, kind: str, expression: Expression, names: List[str], arguments: List[Expression], **kwargs):
        super().__init__(**kwargs)
        self.kind = kind
        self.expression = expression
        self.names = names
        self.arguments = arguments


class FunctionCallOptions(Expression):
    __slots__ = "expression", "names", "options"

    def __init__(self, expression: Expression, names: List[str], options: List[Expression], **kwargs):
        super().__init__(**kwargs)
        self.expression = expression
        self.names = names
        self.options = options


class NewExpression(Expression):
    __slots__ = "typename"

    def __init__(self, typename: TypeName, **kwargs):
        super().__init__(**kwargs)
        self.typename = typename


class MemberAccess(Expression):
    __slots__ = "expression", "member_name"

    def __init__(self, expression: Expression, member_name: str, **kwargs):
        super().__init__(**kwargs)
        self.expression = expression
        self.member_name = member_name


class IndexAccess(Expression):
    __slots__ = "base", "index"

    def __init__(self, base: Expression, index: Optional[Expression], **kwargs):
        super().__init__(**kwargs)
        self.base = base
        self.index = index


class IndexRangeAccess(Expression):
    __slots__ = "base", "start", "end"

    def __init__(self, base: Expression, start: Expression, end: Expression, **kwargs):
        super().__init__(**kwargs)
        self.base = base
        self.start = start
        self.end = end


class Identifier(Expression):
    __slots__ = "name"

    def __init__(self, name: str, **kwargs):
        super().__init__(**kwargs)
        self.name = name


class ElementaryTypeNameExpression(Expression):
    __slots__ = "typename"

    def __init__(self, typename: ElementaryTypeName, **kwargs):
        super().__init__(**kwargs)
        self.typename = typename


class Literal(Expression):
    __slots__ = "kind", "value", "hex_value", "subdenomination"

    def __init__(self, kind: str, value: str, hex_value: str, subdenomination: str, **kwargs):
        super().__init__(**kwargs)
        self.kind = kind
        self.value = value
        self.hex_value = hex_value
        self.subdenomination = subdenomination
