from __future__ import annotations
from typing import List, Optional, Dict, Union, ForwardRef
from pydantic import BaseModel
from pydantic.dataclasses import dataclass


@dataclass
class ASTNode:
    src: str
    id: int


@dataclass
class SourceUnit(ASTNode):
    nodes: List[ASTNode]


@dataclass
class Declaration(ASTNode):
    name: str
    canonical_name: Optional[str]
    visibility: Optional[str]
    referenced_declaration: Optional[int]
    documentation: Optional[str]


@dataclass
class IdentifierPath(Declaration):
    pass


@dataclass
class UserDefinedValueTypeDefinition(Declaration):
    underlying_type: "ElementaryTypeName"
    alias: str


@dataclass
class PragmaDirective(ASTNode):
    literals: List[str]


@dataclass
class UnitAlias:
    name: str


@dataclass
class ImportDirective(ASTNode):
    path: str
    unit_alias: Optional[UnitAlias]
    symbol_aliases: Optional[List[Dict]]


@dataclass
class ContractDefinition(Declaration):
    # kind can be: "interface", "contract", "library", "abstract"
    kind: Optional[str]  # TODO enum
    linearized_base_contracts: Optional[List[int]]
    base_contracts: List["InheritanceSpecifier"]
    nodes: List[ASTNode]


@dataclass
class InheritanceSpecifier(ASTNode):
    basename: Union["UserDefinedTypeName", "IdentifierPath"]
    args: Optional[List["Expression"]]


@dataclass
class UsingForDirective(ASTNode):
    library: Optional[Union["UserDefinedTypeName", "IdentifierPath"]]
    typename: Optional["TypeName"]
    function_list: Optional[List["IdentifierPath"]]
    is_global: bool


@dataclass
class ErrorDefinition(Declaration):
    params: "ParameterList"


@dataclass
class StructDefinition(Declaration):
    members: List["VariableDeclaration"]


@dataclass
class EnumDefinition(Declaration):
    members: List["EnumValue"]


@dataclass
class EnumValue(Declaration):
    pass


@dataclass
class ParameterList(ASTNode):
    params: List["VariableDeclaration"]


@dataclass
class CallableDeclaration(Declaration):
    params: Optional[ParameterList]
    rets: Optional[ParameterList]


# mutability can be: "pure", "view", "nonpayable", "payable"
@dataclass  # kind can be: "function", "constructor", "fallback", "receive"
class FunctionDefinition(CallableDeclaration):
    mutability: str
    kind: str
    modifiers: Optional[List["ModifierInvocation"]]
    body: Optional["Block"]


@dataclass
class VariableDeclaration(Declaration):
    typename: Optional["TypeName"]
    value: Optional["Expression"]
    type_str: str
    mutability: str
    indexed: Optional[bool]
    location: str


@dataclass
class ModifierDefinition(CallableDeclaration):
    body: Optional["Block"]


@dataclass
class ModifierInvocation(ASTNode):
    modifier: Union["Identifier", "IdentifierPath"]
    args: Optional[List["Expression"]]


@dataclass
class EventDefinition(CallableDeclaration):
    anonymous: bool


@dataclass
class TypeName(ASTNode):
    pass


@dataclass
class ElementaryTypeName(TypeName):
    name: str
    mutability: Optional[str]


@dataclass
class UserDefinedTypeName(TypeName):
    name: str
    type_str: str
    referenced_declaration: Optional[int]


@dataclass
class FunctionTypeName(TypeName):
    params: "ParameterList"
    rets: "ParameterList"
    visibility: str
    mutability: str


@dataclass
class Mapping(TypeName):
    key: TypeName
    value: TypeName


@dataclass
class ArrayTypeName(TypeName):
    base: TypeName
    len: Optional["Expression"]


@dataclass
class WildCardTypeName(TypeName):
    name: str


@dataclass
class Statement(ASTNode):
    pass


@dataclass
class InlineAssembly(Statement):
    ast: Optional[Union[Dict, str]]


@dataclass
class Block(Statement):
    statements: List[Statement]


@dataclass
class UncheckedBlock(Block):
    pass


@dataclass
class PlaceholderStatement(Statement):
    pass


@dataclass
class IfStatement(Statement):
    condition: "Expression"
    true_body: Statement
    false_body: Optional[Statement]


@dataclass
class TryCatchClause(ASTNode):
    error_name: str
    block: Block
    params: Optional["ParameterList"]


@dataclass
class TryStatement(Statement):
    external_call: "Expression"
    clauses: List[TryCatchClause]


@dataclass
class WhileStatement(Statement):
    condition: "Expression"
    body: Statement
    is_do_while: bool


@dataclass
class ForStatement(Statement):
    init: Optional[Statement]
    cond: Optional["Expression"]
    loop: Optional["ExpressionStatement"]
    body: Statement


@dataclass
class Continue(Statement):
    pass


@dataclass
class Break(Statement):
    pass


@dataclass
class Return(Statement):
    expression: Optional["Expression"]


@dataclass
class Revert(Statement):
    error_call: "FunctionCall"


@dataclass
class Throw(Statement):
    pass


@dataclass
class EmitStatement(Statement):
    event_call: "FunctionCall"


@dataclass
class VariableDeclarationStatement(Statement):
    variables: List[Optional["VariableDeclaration"]]
    initial_value: Optional["Expression"]


@dataclass
class ExpressionStatement(Statement):
    expression: "Expression"


@dataclass
class Expression(ASTNode):
    type_str: str
    constant: bool
    pure: bool


@dataclass
class Conditional(Expression):
    condition: Expression
    true_expr: Expression
    false_expr: Expression


@dataclass
class Assignment(Expression):
    left: Expression
    operator: str
    right: Expression


@dataclass
class TupleExpression(Expression):
    components: List[Optional[Expression]]
    is_array: bool


@dataclass
class UnaryOperation(Expression):
    operator: str
    expression: Expression
    is_prefix: bool


@dataclass
class BinaryOperation(Expression):
    left: Expression
    operator: str
    right: Expression


@dataclass  # kind can be: "functionCall", "typeConversion", "structConstructorCall"
class FunctionCall(Expression):
    kind: str
    expression: Expression
    names: List[Optional[str]]
    arguments: List[Expression]


@dataclass
class FunctionCallOptions(Expression):
    expression: Expression
    names: List[str]
    options: List[Expression]


@dataclass
class NewExpression(Expression):
    typename: TypeName


@dataclass
class MemberAccess(Expression):
    expression: Expression
    member_name: str


@dataclass
class IndexAccess(Expression):
    base: Expression
    index: Optional[Expression]


@dataclass
class IndexRangeAccess(Expression):
    base: Expression
    start: Optional[Expression]
    end: Optional[Expression]


@dataclass
class Identifier(Expression):
    name: str
    referenced_declaration: Optional[int]


@dataclass
class ElementaryTypeNameExpression(Expression):
    typename: ElementaryTypeName


@dataclass
class Literal(Expression):
    kind: Optional[str]
    value: Optional[str]
    hex_value: str
    subdenomination: Optional[str]


VariableDeclaration.__pydantic_model__.update_forward_refs()
VariableDeclarationStatement.__pydantic_model__.update_forward_refs()
ExpressionStatement.__pydantic_model__.update_forward_refs()
IfStatement.__pydantic_model__.update_forward_refs()
ParameterList.__pydantic_model__.update_forward_refs()
FunctionDefinition.__pydantic_model__.update_forward_refs()
ContractDefinition.__pydantic_model__.update_forward_refs()
Return.__pydantic_model__.update_forward_refs()
UsingForDirective.__pydantic_model__.update_forward_refs()
EmitStatement.__pydantic_model__.update_forward_refs()
ArrayTypeName.__pydantic_model__.update_forward_refs()
StructDefinition.__pydantic_model__.update_forward_refs()
ForStatement.__pydantic_model__.update_forward_refs()
WhileStatement.__pydantic_model__.update_forward_refs()
ModifierDefinition.__pydantic_model__.update_forward_refs()
ModifierInvocation.__pydantic_model__.update_forward_refs()
InheritanceSpecifier.__pydantic_model__.update_forward_refs()
ErrorDefinition.__pydantic_model__.update_forward_refs()
EnumDefinition.__pydantic_model__.update_forward_refs()
Revert.__pydantic_model__.update_forward_refs()
TryStatement.__pydantic_model__.update_forward_refs()
UserDefinedValueTypeDefinition.__pydantic_model__.update_forward_refs()
