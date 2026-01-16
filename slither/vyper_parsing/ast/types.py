from __future__ import annotations
from dataclasses import dataclass


@dataclass(slots=True)
class ASTNode:
    src: str
    node_id: int


@dataclass(slots=True)
class Definition(ASTNode):
    doc_string: str | None


@dataclass(slots=True)
class Module(Definition):
    body: list[ASTNode]
    name: str


@dataclass(slots=True)
class ImportFrom(ASTNode):
    module: str
    name: str
    alias: str | None


@dataclass(slots=True)
class EventDef(ASTNode):
    name: str
    body: list[AnnAssign]


@dataclass(slots=True)
class AnnAssign(ASTNode):
    target: Name
    annotation: Subscript | Name | Call
    value: ASTNode | None


@dataclass(slots=True)
class Name(ASTNode):  # type or identifier
    id: str


@dataclass(slots=True)
class Call(ASTNode):
    func: ASTNode
    args: list[ASTNode]
    keyword: ASTNode | None
    keywords: list[ASTNode]


@dataclass(slots=True)
class Pass(ASTNode):
    pass


@dataclass(slots=True)
class StructDef(ASTNode):
    name: str
    body: list[AnnAssign]


@dataclass(slots=True)
class VariableDecl(ASTNode):
    annotation: ASTNode
    target: ASTNode
    value: ASTNode | None
    is_constant: bool
    is_immutable: bool
    is_public: bool


@dataclass(slots=True)
class Subscript(ASTNode):
    value: ASTNode
    slice: ASTNode


@dataclass(slots=True)
class Index(ASTNode):
    value: ASTNode


@dataclass(slots=True)
class Bytes(ASTNode):
    value: bytes


@dataclass(slots=True)
class Hex(ASTNode):
    value: str


@dataclass(slots=True)
class Int(ASTNode):
    value: int


@dataclass(slots=True)
class Str(ASTNode):
    value: str


@dataclass(slots=True)
class VyList(ASTNode):
    elements: list[ASTNode]


@dataclass(slots=True)
class VyDict(ASTNode):
    keys: list[ASTNode]
    values: list[ASTNode]


@dataclass(slots=True)
class Tuple(ASTNode):
    elements: list[ASTNode]


@dataclass(slots=True)
class FunctionDef(Definition):
    name: str
    args: Arguments | None
    returns: list[ASTNode] | None
    body: list[ASTNode]
    decorators: list[ASTNode] | None
    pos: any | None  # not sure what this is


@dataclass(slots=True)
class Assign(ASTNode):
    target: ASTNode
    value: ASTNode


@dataclass(slots=True)
class Attribute(ASTNode):
    value: ASTNode
    attr: str


@dataclass(slots=True)
class Arguments(ASTNode):
    args: list[Arg]
    default: ASTNode | None
    defaults: list[ASTNode]


@dataclass(slots=True)
class Arg(ASTNode):
    arg: str
    annotation: ASTNode | None


@dataclass(slots=True)
class Assert(ASTNode):
    test: ASTNode
    msg: Str | None


@dataclass(slots=True)
class Raise(ASTNode):
    exc: ASTNode


@dataclass(slots=True)
class Expr(ASTNode):
    value: ASTNode


@dataclass(slots=True)
class UnaryOp(ASTNode):
    op: ASTNode
    operand: ASTNode


@dataclass(slots=True)
class BinOp(ASTNode):
    left: ASTNode
    op: str
    right: ASTNode


@dataclass(slots=True)
class Keyword(ASTNode):
    arg: str
    value: ASTNode


@dataclass(slots=True)
class Log(ASTNode):
    value: ASTNode


@dataclass(slots=True)
class Return(ASTNode):
    value: ASTNode | None


@dataclass(slots=True)
class If(ASTNode):
    test: ASTNode
    body: list[ASTNode]
    orelse: list[ASTNode]


@dataclass(slots=True)
class Compare(ASTNode):
    left: ASTNode
    op: ASTNode
    right: ASTNode


@dataclass(slots=True)
class NameConstant(ASTNode):
    value: bool


@dataclass(slots=True)
class For(ASTNode):
    target: ASTNode
    iter: ASTNode
    body: list[ASTNode]


@dataclass(slots=True)
class Continue(ASTNode):
    pass


@dataclass(slots=True)
class Break(ASTNode):
    pass


@dataclass(slots=True)
class InterfaceDef(ASTNode):
    name: str
    body: list[ASTNode]


@dataclass(slots=True)
class EnumDef(ASTNode):
    name: str
    body: list[ASTNode]


@dataclass(slots=True)
class AugAssign(ASTNode):
    target: ASTNode
    op: ASTNode
    value: ASTNode


@dataclass(slots=True)
class BoolOp(ASTNode):
    op: ASTNode
    values: list[ASTNode]
