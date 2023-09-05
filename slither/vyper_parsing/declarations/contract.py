from pathlib import Path
from typing import List, TYPE_CHECKING
from slither.vyper_parsing.ast.types import (
    Module,
    FunctionDef,
    EventDef,
    EnumDef,
    StructDef,
    VariableDecl,
    ImportFrom,
    InterfaceDef,
    AnnAssign,
    Expr,
    Name,
    Arguments,
    Index,
    Subscript,
    Int,
    Arg,
)

from slither.vyper_parsing.declarations.event import EventVyper
from slither.vyper_parsing.declarations.struct import StructVyper
from slither.vyper_parsing.variables.state_variable import StateVariableVyper
from slither.vyper_parsing.declarations.function import FunctionVyper
from slither.core.declarations.function_contract import FunctionContract
from slither.core.declarations import Contract, StructureContract, EnumContract, Event

from slither.core.variables.state_variable import StateVariable

if TYPE_CHECKING:
    from slither.vyper_parsing.vyper_compilation_unit import VyperCompilationUnit


class ContractVyper:  # pylint: disable=too-many-instance-attributes
    def __init__(
        self, slither_parser: "VyperCompilationUnit", contract: Contract, module: Module
    ) -> None:

        self._contract: Contract = contract
        self._slither_parser: "VyperCompilationUnit" = slither_parser
        self._data = module
        # Vyper models only have one contract (aside from interfaces) and the name is the file path
        # We use the stem to make it a more user friendly name that is easy to query via canonical name
        self._contract.name = Path(module.name).stem
        self._contract.id = module.node_id
        self._is_analyzed: bool = False

        self._enumsNotParsed: List[EnumDef] = []
        self._structuresNotParsed: List[StructDef] = []
        self._variablesNotParsed: List[VariableDecl] = []
        self._eventsNotParsed: List[EventDef] = []
        self._functionsNotParsed: List[FunctionDef] = []

        self._structures_parser: List[StructVyper] = []
        self._variables_parser: List[StateVariableVyper] = []
        self._events_parser: List[EventVyper] = []
        self._functions_parser: List[FunctionVyper] = []

        self._parse_contract_items()

    @property
    def is_analyzed(self) -> bool:
        return self._is_analyzed

    def set_is_analyzed(self, is_analyzed: bool) -> None:
        self._is_analyzed = is_analyzed

    @property
    def underlying_contract(self) -> Contract:
        return self._contract

    def _parse_contract_items(self) -> None:
        for node in self._data.body:
            if isinstance(node, FunctionDef):
                self._functionsNotParsed.append(node)
            elif isinstance(node, EventDef):
                self._eventsNotParsed.append(node)
            elif isinstance(node, VariableDecl):
                self._variablesNotParsed.append(node)
            elif isinstance(node, EnumDef):
                self._enumsNotParsed.append(node)
            elif isinstance(node, StructDef):
                self._structuresNotParsed.append(node)
            elif isinstance(node, ImportFrom):
                # TOOD aliases
                # We create an `InterfaceDef` sense the compilatuion unit does not contain the actual interface
                # https://github.com/vyperlang/vyper/tree/master/vyper/builtins/interfaces
                if node.module == "vyper.interfaces":
                    interfaces = {
                        "ERC20Detailed": InterfaceDef(
                            src="-1:-1:-1",
                            node_id=-1,
                            name="ERC20Detailed",
                            body=[
                                FunctionDef(
                                    src="-1:-1:-1",
                                    node_id=-1,
                                    doc_string=None,
                                    name="name",
                                    args=Arguments(
                                        src="-1:-1:-1",
                                        node_id=-1,
                                        args=[],
                                        default=None,
                                        defaults=[],
                                    ),
                                    returns=Subscript(
                                        src="-1:-1:-1",
                                        node_id=-1,
                                        value=Name(src="-1:-1:-1", node_id=-1, id="String"),
                                        slice=Index(
                                            src="-1:-1:-1",
                                            node_id=-1,
                                            value=Int(src="-1:-1:-1", node_id=-1, value=1),
                                        ),
                                    ),
                                    body=[
                                        Expr(
                                            src="-1:-1:-1",
                                            node_id=-1,
                                            value=Name(src="-1:-1:-1", node_id=-1, id="view"),
                                        )
                                    ],
                                    decorators=[],
                                    pos=None,
                                ),
                                FunctionDef(
                                    src="-1:-1:-1",
                                    node_id=-1,
                                    doc_string=None,
                                    name="symbol",
                                    args=Arguments(
                                        src="-1:-1:-1",
                                        node_id=-1,
                                        args=[],
                                        default=None,
                                        defaults=[],
                                    ),
                                    returns=Subscript(
                                        src="-1:-1:-1",
                                        node_id=-1,
                                        value=Name(src="-1:-1:-1", node_id=-1, id="String"),
                                        slice=Index(
                                            src="-1:-1:-1",
                                            node_id=-1,
                                            value=Int(src="-1:-1:-1", node_id=-1, value=1),
                                        ),
                                    ),
                                    body=[
                                        Expr(
                                            src="-1:-1:-1",
                                            node_id=-1,
                                            value=Name(src="-1:-1:-1", node_id=-1, id="view"),
                                        )
                                    ],
                                    decorators=[],
                                    pos=None,
                                ),
                                FunctionDef(
                                    src="-1:-1:-1",
                                    node_id=-1,
                                    doc_string=None,
                                    name="decimals",
                                    args=Arguments(
                                        src="-1:-1:-1",
                                        node_id=-1,
                                        args=[],
                                        default=None,
                                        defaults=[],
                                    ),
                                    returns=Name(src="-1:-1:-1", node_id=-1, id="uint8"),
                                    body=[
                                        Expr(
                                            src="-1:-1:-1",
                                            node_id=-1,
                                            value=Name(src="-1:-1:-1", node_id=-1, id="view"),
                                        )
                                    ],
                                    decorators=[],
                                    pos=None,
                                ),
                            ],
                        ),
                        "ERC20": InterfaceDef(
                            src="-1:-1:-1",
                            node_id=1,
                            name="ERC20",
                            body=[
                                FunctionDef(
                                    src="-1:-1:-1",
                                    node_id=2,
                                    doc_string=None,
                                    name="totalSupply",
                                    args=Arguments(
                                        src="-1:-1:-1",
                                        node_id=3,
                                        args=[],
                                        default=None,
                                        defaults=[],
                                    ),
                                    returns=Name(src="-1:-1:-1", node_id=7, id="uint256"),
                                    body=[
                                        Expr(
                                            src="-1:-1:-1",
                                            node_id=4,
                                            value=Name(src="-1:-1:-1", node_id=5, id="view"),
                                        )
                                    ],
                                    decorators=[],
                                    pos=None,
                                ),
                                FunctionDef(
                                    src="-1:-1:-1",
                                    node_id=9,
                                    doc_string=None,
                                    name="balanceOf",
                                    args=Arguments(
                                        src="-1:-1:-1",
                                        node_id=10,
                                        args=[
                                            Arg(
                                                src="-1:-1:-1",
                                                node_id=11,
                                                arg="_owner",
                                                annotation=Name(
                                                    src="-1:-1:-1", node_id=12, id="address"
                                                ),
                                            )
                                        ],
                                        default=None,
                                        defaults=[],
                                    ),
                                    returns=Name(src="-1:-1:-1", node_id=17, id="uint256"),
                                    body=[
                                        Expr(
                                            src="-1:-1:-1",
                                            node_id=14,
                                            value=Name(src="-1:-1:-1", node_id=15, id="view"),
                                        )
                                    ],
                                    decorators=[],
                                    pos=None,
                                ),
                                FunctionDef(
                                    src="-1:-1:-1",
                                    node_id=19,
                                    doc_string=None,
                                    name="allowance",
                                    args=Arguments(
                                        src="-1:-1:-1",
                                        node_id=20,
                                        args=[
                                            Arg(
                                                src="-1:-1:-1",
                                                node_id=21,
                                                arg="_owner",
                                                annotation=Name(
                                                    src="-1:-1:-1", node_id=22, id="address"
                                                ),
                                            ),
                                            Arg(
                                                src="-1:-1:-1",
                                                node_id=24,
                                                arg="_spender",
                                                annotation=Name(
                                                    src="-1:-1:-1", node_id=25, id="address"
                                                ),
                                            ),
                                        ],
                                        default=None,
                                        defaults=[],
                                    ),
                                    returns=Name(src="-1:-1:-1", node_id=30, id="uint256"),
                                    body=[
                                        Expr(
                                            src="-1:-1:-1",
                                            node_id=27,
                                            value=Name(src="-1:-1:-1", node_id=28, id="view"),
                                        )
                                    ],
                                    decorators=[],
                                    pos=None,
                                ),
                                FunctionDef(
                                    src="-1:-1:-1",
                                    node_id=32,
                                    doc_string=None,
                                    name="transfer",
                                    args=Arguments(
                                        src="-1:-1:-1",
                                        node_id=33,
                                        args=[
                                            Arg(
                                                src="-1:-1:-1",
                                                node_id=34,
                                                arg="_to",
                                                annotation=Name(
                                                    src="-1:-1:-1", node_id=35, id="address"
                                                ),
                                            ),
                                            Arg(
                                                src="-1:-1:-1",
                                                node_id=37,
                                                arg="_value",
                                                annotation=Name(
                                                    src="-1:-1:-1", node_id=38, id="uint256"
                                                ),
                                            ),
                                        ],
                                        default=None,
                                        defaults=[],
                                    ),
                                    returns=Name(src="-1:-1:-1", node_id=43, id="bool"),
                                    body=[
                                        Expr(
                                            src="-1:-1:-1",
                                            node_id=40,
                                            value=Name(src="-1:-1:-1", node_id=41, id="nonpayable"),
                                        )
                                    ],
                                    decorators=[],
                                    pos=None,
                                ),
                                FunctionDef(
                                    src="-1:-1:-1",
                                    node_id=45,
                                    doc_string=None,
                                    name="transferFrom",
                                    args=Arguments(
                                        src="-1:-1:-1",
                                        node_id=46,
                                        args=[
                                            Arg(
                                                src="-1:-1:-1",
                                                node_id=47,
                                                arg="_from",
                                                annotation=Name(
                                                    src="-1:-1:-1", node_id=48, id="address"
                                                ),
                                            ),
                                            Arg(
                                                src="-1:-1:-1",
                                                node_id=50,
                                                arg="_to",
                                                annotation=Name(
                                                    src="-1:-1:-1", node_id=51, id="address"
                                                ),
                                            ),
                                            Arg(
                                                src="-1:-1:-1",
                                                node_id=53,
                                                arg="_value",
                                                annotation=Name(
                                                    src="-1:-1:-1", node_id=54, id="uint256"
                                                ),
                                            ),
                                        ],
                                        default=None,
                                        defaults=[],
                                    ),
                                    returns=Name(src="-1:-1:-1", node_id=59, id="bool"),
                                    body=[
                                        Expr(
                                            src="-1:-1:-1",
                                            node_id=56,
                                            value=Name(src="-1:-1:-1", node_id=57, id="nonpayable"),
                                        )
                                    ],
                                    decorators=[],
                                    pos=None,
                                ),
                                FunctionDef(
                                    src="-1:-1:-1",
                                    node_id=61,
                                    doc_string=None,
                                    name="approve",
                                    args=Arguments(
                                        src="-1:-1:-1",
                                        node_id=62,
                                        args=[
                                            Arg(
                                                src="-1:-1:-1",
                                                node_id=63,
                                                arg="_spender",
                                                annotation=Name(
                                                    src="-1:-1:-1", node_id=64, id="address"
                                                ),
                                            ),
                                            Arg(
                                                src="-1:-1:-1",
                                                node_id=66,
                                                arg="_value",
                                                annotation=Name(
                                                    src="-1:-1:-1", node_id=67, id="uint256"
                                                ),
                                            ),
                                        ],
                                        default=None,
                                        defaults=[],
                                    ),
                                    returns=Name(src="-1:-1:-1", node_id=72, id="bool"),
                                    body=[
                                        Expr(
                                            src="-1:-1:-1",
                                            node_id=69,
                                            value=Name(src="-1:-1:-1", node_id=70, id="nonpayable"),
                                        )
                                    ],
                                    decorators=[],
                                    pos=None,
                                ),
                            ],
                        ),
                        "ERC165": [],
                        "ERC721": [],
                        "ERC4626": [],
                    }
                    self._data.body.append(interfaces[node.name])

            elif isinstance(node, InterfaceDef):
                # This needs to be done lazily as interfaces can refer to constant state variables
                contract = Contract(self._contract.compilation_unit, self._contract.file_scope)
                contract.set_offset(node.src, self._contract.compilation_unit)
                contract.is_interface = True

                contract_parser = ContractVyper(self._slither_parser, contract, node)
                self._contract.file_scope.contracts[contract.name] = contract
                # pylint: disable=protected-access
                self._slither_parser._underlying_contract_to_parser[contract] = contract_parser

            elif isinstance(node, AnnAssign):  # implements: ERC20
                pass  # TODO
            else:
                raise ValueError("Unknown contract node: ", node)

    def parse_enums(self) -> None:
        for enum in self._enumsNotParsed:
            name = enum.name
            canonicalName = self._contract.name + "." + enum.name
            values = [x.value.id for x in enum.body]
            new_enum = EnumContract(name, canonicalName, values)
            new_enum.set_contract(self._contract)
            new_enum.set_offset(enum.src, self._contract.compilation_unit)
            self._contract.enums_as_dict[name] = new_enum  # TODO solidity using canonicalName
        self._enumsNotParsed = []

    def parse_structs(self) -> None:
        for struct in self._structuresNotParsed:
            st = StructureContract(self._contract.compilation_unit)
            st.set_contract(self._contract)
            st.set_offset(struct.src, self._contract.compilation_unit)

            st_parser = StructVyper(st, struct)
            self._contract.structures_as_dict[st.name] = st
            self._structures_parser.append(st_parser)
            # Interfaces can refer to struct defs
            self._contract.file_scope.structures[st.name] = st

        self._structuresNotParsed = []

    def parse_state_variables(self) -> None:
        for varNotParsed in self._variablesNotParsed:
            var = StateVariable()
            var.set_contract(self._contract)
            var.set_offset(varNotParsed.src, self._contract.compilation_unit)

            var_parser = StateVariableVyper(var, varNotParsed)
            self._variables_parser.append(var_parser)

            assert var.name
            self._contract.variables_as_dict[var.name] = var
            self._contract.add_variables_ordered([var])
            # Interfaces can refer to constants
            self._contract.file_scope.variables[var.name] = var

        self._variablesNotParsed = []

    def parse_events(self) -> None:
        for event_to_parse in self._eventsNotParsed:
            event = Event()
            event.set_contract(self._contract)
            event.set_offset(event_to_parse.src, self._contract.compilation_unit)

            event_parser = EventVyper(event, event_to_parse)
            self._events_parser.append(event_parser)
            self._contract.events_as_dict[event.full_name] = event

    def parse_functions(self) -> None:

        for function in self._functionsNotParsed:
            func = FunctionContract(self._contract.compilation_unit)
            func.set_offset(function.src, self._contract.compilation_unit)
            func.set_contract(self._contract)
            func.set_contract_declarer(self._contract)

            func_parser = FunctionVyper(func, function, self)
            self._contract.add_function(func)
            self._contract.compilation_unit.add_function(func)
            self._functions_parser.append(func_parser)

        self._functionsNotParsed = []

    def analyze_state_variables(self):
        # Struct defs can refer to constant state variables
        for var_parser in self._variables_parser:
            var_parser.analyze(self._contract)

    def analyze(self) -> None:

        for struct_parser in self._structures_parser:
            struct_parser.analyze(self._contract)

        for event_parser in self._events_parser:
            event_parser.analyze(self._contract)

        for function in self._functions_parser:
            function.analyze_params()

        for function in self._functions_parser:
            function.analyze_content()

    def __hash__(self) -> int:
        return self._contract.id
