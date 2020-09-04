"""
    Event module
"""
from typing import Dict, TYPE_CHECKING

from slither.core.cfg.node import NodeType
from slither.core.cfg.node import link_nodes
from slither.core.declarations.modifier import Modifier
from slither.solc_parsing.cfg.node import NodeSolc
from slither.solc_parsing.declarations.function import FunctionSolc

if TYPE_CHECKING:
    from slither.solc_parsing.declarations.contract import ContractSolc


class ModifierSolc(FunctionSolc):
    def __init__(self, modifier: Modifier, function_data: Dict, contract_parser: "ContractSolc"):
        super().__init__(modifier, function_data, contract_parser)
        # _modifier is equal to _function, but keep it here to prevent
        # confusion for mypy in underlying_function
        self._modifier = modifier

    @property
    def underlying_function(self) -> Modifier:
        return self._modifier

    def analyze_params(self):
        # Can be re-analyzed due to inheritance
        if self._params_was_analyzed:
            return

        self._params_was_analyzed = True

        self._analyze_attributes()

        if self.is_compact_ast:
            params = self._functionNotParsed["parameters"]
        else:
            children = self._functionNotParsed["children"]
            params = children[0]

        if params:
            self._parse_params(params)

    def analyze_content(self):
        if self._content_was_analyzed:
            return

        self._content_was_analyzed = True

        if self.is_compact_ast:
            body = self._functionNotParsed["body"]

            if body and body[self.get_key()] == "Block":
                self._function.is_implemented = True
                self._parse_cfg(body)

        else:
            children = self._functionNotParsed["children"]

            self._function.is_implemented = False
            if len(children) > 1:
                assert len(children) == 2
                block = children[1]
                assert block["name"] == "Block"
                self._function.is_implemented = True
                self._parse_cfg(block)

        for local_var_parser in self._local_variables_parser:
            local_var_parser.analyze(self)

        for node in self._node_to_nodesolc.values():
            node.analyze_expressions(self)

        self._filter_ternary()
        self._remove_alone_endif()

        # self._analyze_read_write()
        # self._analyze_calls()

    def _parse_statement(self, statement: Dict, node: NodeSolc) -> NodeSolc:
        name = statement[self.get_key()]
        if name == "PlaceholderStatement":
            placeholder_node = self._new_node(NodeType.PLACEHOLDER, statement["src"])
            link_nodes(node.underlying_node, placeholder_node.underlying_node)
            return placeholder_node
        return super()._parse_statement(statement, node)
