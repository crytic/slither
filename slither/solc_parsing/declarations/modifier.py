"""
    Event module
"""
from typing import TYPE_CHECKING

from slither.core.cfg.node import NodeType
from slither.core.cfg.node import link_nodes
from slither.core.declarations.modifier import Modifier
from slither.solc_parsing.cfg.node import NodeSolc
from slither.solc_parsing.declarations.function import FunctionSolc
from slither.solc_parsing.types.types import ModifierDefinition, ASTNode, PlaceholderStatement

if TYPE_CHECKING:
    from slither.solc_parsing.declarations.contract import ContractSolc


class ModifierSolc(FunctionSolc):
    def __init__(self, modifier: Modifier, function_data: ModifierDefinition, contract_parser: "ContractSolc"):
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

        if self._functionNotParsed.params:
            self._parse_params(self._functionNotParsed.params)

    def analyze_content(self):
        if self._content_was_analyzed:
            return

        self._content_was_analyzed = True

        self._function.is_implemented = True
        self._parse_cfg(self._functionNotParsed.body)

        for local_var_parser in self._local_variables_parser:
            local_var_parser.analyze(self)

        for node in self._node_to_nodesolc.values():
            node.analyze_expressions(self)

        self._filter_ternary()
        self._remove_alone_endif()

    def _parse(self, stmt: ASTNode, node: NodeSolc) -> NodeSolc:
        if isinstance(stmt, PlaceholderStatement):
            placeholder_node = self._new_node(NodeType.PLACEHOLDER, stmt.src)
            link_nodes(node.underlying_node, placeholder_node.underlying_node)
            return placeholder_node
        return super()._parse(stmt, node)
