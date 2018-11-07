"""
    Event module
"""
from slither.core.declarations.modifier import Modifier
from slither.solc_parsing.declarations.function import FunctionSolc

from slither.core.cfg.node import NodeType
from slither.core.cfg.node import link_nodes

class ModifierSolc(Modifier, FunctionSolc):


    def analyze_params(self):
        # Can be re-analyzed due to inheritance
        if self._params_was_analyzed:
            return

        self._params_was_analyzed = True

        self._analyze_attributes()

        if self.is_compact_ast:
            params = self._functionNotParsed['parameters']
        else:
            children = self._functionNotParsed['children']
            params = children[0]

        if params:
            self._parse_params(params)

    def analyze_content(self):
        if self._content_was_analyzed:
            return

        self._content_was_analyzed = True


        if self.is_compact_ast:
            body = self._functionNotParsed['body']

            if body and body[self.get_key()] == 'Block':
                self._is_implemented = True
                self._parse_cfg(body)

        else:
            children = self._functionNotParsed['children']

            self._isImplemented = False
            if len(children) > 1:
                assert len(children) == 2
                block = children[1]
                assert block['name'] == 'Block'
                self._isImplemented = True
                self._parse_cfg(block)

        for local_vars in self.variables:
            local_vars.analyze(self)

        for node in self.nodes:
            node.analyze_expressions(self)

        self._analyze_read_write()
        self._analyze_calls()

    def _parse_statement(self, statement, node):
        name = statement[self.get_key()]
        if name == 'PlaceholderStatement':
            placeholder_node = self._new_node(NodeType.PLACEHOLDER, statement['src'])
            link_nodes(node, placeholder_node)
            return placeholder_node
        return super(ModifierSolc, self)._parse_statement(statement, node)
