from __future__ import annotations
from typing import List, Optional, Union
from dataclasses import dataclass


@dataclass
class ASTNode:
    src: str
    node_id: int


@dataclass
class Definition(ASTNode):
    doc_string: Optional[str]


@dataclass
class Module(Definition):
    body: List[ASTNode]
    name: str


@dataclass
class ImportFrom(ASTNode):
    module: str
    name: str
    alias: Optional[str]


@dataclass
class EventDef(ASTNode):
    name: str
    body: List[AnnAssign]


@dataclass
class AnnAssign(ASTNode):
    target: Name
    annotation: Union[Subscript, Name, Call]
    value: Optional[ASTNode]


@dataclass
class Name(ASTNode):  # type or identifier
    id: str


@dataclass
class Call(ASTNode):
    func: ASTNode
    args: List[ASTNode]
    keyword: Optional[ASTNode]
    keywords: List[ASTNode]


@dataclass
class Pass(ASTNode):
    pass


@dataclass
class StructDef(ASTNode):
    name: str
    body: List[AnnAssign]


@dataclass
class VariableDecl(ASTNode):
    annotation: ASTNode
    target: ASTNode
    value: Optional[ASTNode]
    is_constant: bool
    is_immutable: bool
    is_public: bool


@dataclass
class Subscript(ASTNode):
    value: ASTNode
    slice: ASTNode


@dataclass
class Index(ASTNode):
    value: ASTNode


@dataclass
class Bytes(ASTNode):
    value: bytes


@dataclass
class Hex(ASTNode):
    value: str


@dataclass
class Int(ASTNode):
    value: int


@dataclass
class Str(ASTNode):
    value: str


@dataclass
class VyList(ASTNode):
    elements: List[ASTNode]


@dataclass
class VyDict(ASTNode):
    keys: List[ASTNode]
    values: List[ASTNode]


@dataclass
class Tuple(ASTNode):
    elements: List[ASTNode]


@dataclass
class FunctionDef(Definition):
    name: str
    args: Optional[Arguments]
    returns: Optional[List[ASTNode]]
    body: List[ASTNode]
    decorators: Optional[List[ASTNode]]
    pos: Optional[any]  # not sure what this is


@dataclass
class Assign(ASTNode):
    target: ASTNode
    value: ASTNode


@dataclass
class Attribute(ASTNode):
    value: ASTNode
    attr: str


@dataclass
class Arguments(ASTNode):
    args: List[Arg]
    default: Optional[ASTNode]
    defaults: List[ASTNode]


@dataclass
class Arg(ASTNode):
    arg: str
    annotation: Optional[ASTNode]


@dataclass
class Assert(ASTNode):
    test: ASTNode
    msg: Optional[Str]


@dataclass
class Raise(ASTNode):
    exc: ASTNode


@dataclass
class Expr(ASTNode):
    value: ASTNode


@dataclass
class UnaryOp(ASTNode):
    op: ASTNode
    operand: ASTNode


@dataclass
class BinOp(ASTNode):
    left: ASTNode
    op: str
    right: ASTNode


@dataclass
class Keyword(ASTNode):
    arg: str
    value: ASTNode


@dataclass
class Log(ASTNode):
    value: ASTNode


@dataclass
class Return(ASTNode):
    value: Optional[ASTNode]


@dataclass
class If(ASTNode):
    test: ASTNode
    body: List[ASTNode]
    orelse: List[ASTNode]


@dataclass
class Compare(ASTNode):
    left: ASTNode
    op: ASTNode
    right: ASTNode


@dataclass
class NameConstant(ASTNode):
    value: bool


@dataclass
class For(ASTNode):
    target: ASTNode
    iter: ASTNode
    body: List[ASTNode]


@dataclass
class Continue(ASTNode):
    pass


@dataclass
class Break(ASTNode):
    pass


@dataclass
class InterfaceDef(ASTNode):
    name: str
    body: List[ASTNode]


@dataclass
class EnumDef(ASTNode):
    name: str
    body: List[ASTNode]


@dataclass
class AugAssign(ASTNode):
    target: ASTNode
    op: ASTNode
    value: ASTNode


@dataclass
class BoolOp(ASTNode):
    op: ASTNode
    values: List[ASTNode]
