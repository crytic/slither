"""
    Event module
"""
import logging
from slither.core.declarations.function import Function
from slither.core.cfg.node import NodeType
from slither.solc_parsing.cfg.node import NodeSolc
from slither.core.cfg.node import NodeType
from slither.core.cfg.node import link_nodes

from slither.solc_parsing.variables.local_variable import LocalVariableSolc
from slither.solc_parsing.variables.local_variable_init_from_tuple import LocalVariableInitFromTupleSolc
from slither.solc_parsing.variables.variable_declaration import MultipleVariablesDeclaration

from slither.solc_parsing.expressions.expression_parsing import parse_expression

from slither.visitors.expression.export_values import ExportValues
from slither.visitors.expression.has_conditional import HasConditional

from slither.utils.expression_manipulations import SplitTernaryExpression


logger = logging.getLogger("FunctionSolc")

class FunctionSolc(Function):
    """
    Event class
    """
    # elems = [(type, name)]

    def __init__(self, function):
        super(FunctionSolc, self).__init__()
        self._name = function['attributes']['name']
        self._functionNotParsed = function
        self._params_was_analyzed = False
        self._content_was_analyzed = False
        self._counter_nodes = 0

    def _analyze_attributes(self):
        attributes = self._functionNotParsed['attributes']

        if 'payable' in attributes:
            self._payable = attributes['payable']
        elif 'stateMutability' in attributes:
            if attributes['stateMutability'] == 'payable':
                self._payable = True
            elif attributes['stateMutability'] == 'pure':
                self._pure = True
                self._view = True

        if 'constant' in attributes:
            self._view = attributes['constant']

        self._is_constructor = False

        if 'isConstructor' in attributes:
            self._is_constructor = attributes['isConstructor']

        if 'visibility' in attributes:
            self._visibility = attributes['visibility']
        # old solc
        elif 'public' in attributes:
            if attributes['public']:
                self._visibility = 'public'
            else:
                self._visibility = 'private'
        else:
            self._visibility = 'public'

        if 'payable' in attributes:
            self._payable = attributes['payable']

    def _new_node(self, node_type):
        node = NodeSolc(node_type, self._counter_nodes)
        self._counter_nodes += 1
        node.set_function(self)
        self._nodes.append(node)
        return node

    def _parse_if(self, ifStatement, node):
        # IfStatement = 'if' '(' Expression ')' Statement ( 'else' Statement )?

        children = ifStatement['children']
        condition_node = self._new_node(NodeType.IF)
        #condition = parse_expression(children[0], self)
        condition = children[0]
        condition_node.add_unparsed_expression(condition)

        link_nodes(node, condition_node)

        trueStatement = self._parse_statement(children[1], condition_node)

        endIf_node = self._new_node(NodeType.ENDIF)
        link_nodes(trueStatement, endIf_node)

        if len(children) == 3:
            falseStatement = self._parse_statement(children[2], condition_node)

            link_nodes(falseStatement, endIf_node)

        else:
            link_nodes(condition_node, endIf_node)

        return endIf_node

    def _parse_while(self, whileStatement, node):
        # WhileStatement = 'while' '(' Expression ')' Statement

        children = whileStatement['children']

        node_startWhile = self._new_node(NodeType.STARTLOOP)

        node_condition = self._new_node(NodeType.IFLOOP)
        #expression = parse_expression(children[0], self)
        expression = children[0]
        node_condition.add_unparsed_expression(expression)

        statement = self._parse_statement(children[1], node_condition)

        node_endWhile = self._new_node(NodeType.ENDLOOP)

        link_nodes(node, node_startWhile)
        link_nodes(node_startWhile, node_condition)
        link_nodes(statement, node_condition)
        link_nodes(node_condition, node_endWhile)

        return node_endWhile

    def _parse_for(self, statement, node):
        # ForStatement = 'for' '(' (SimpleStatement)? ';' (Expression)? ';' (ExpressionStatement)? ')' Statement

        hasInitExession = True
        hasCondition = True
        hasLoopExpression = True

        # Old solc version do not prevent in the attributes
        # if the loop has a init value /condition or expression
        # There is no way to determine that for(a;;) and for(;a;) are different with old solc
        if 'attributes' in statement:
            if 'initializationExpression' in statement:
                if not statement['initializationExpression']:
                    hasInitExession = False
            if 'condition' in statement:
                if not statement['condition']:
                    hasCondition = False
            if 'loopExpression' in statement:
                if not statement['loopExpression']:
                    hasLoopExpression = False


        node_startLoop = self._new_node(NodeType.STARTLOOP)
        node_endLoop = self._new_node(NodeType.ENDLOOP)

        children = statement['children']

        if hasInitExession:
            if len(children) >= 2:
                if children[0]['name'] in ['VariableDefinitionStatement',
                                           'VariableDeclarationStatement',
                                           'ExpressionStatement']:
                    node_initExpression = self._parse_statement(children[0], node)
                    link_nodes(node_initExpression, node_startLoop)
                else:
                    hasInitExession = False
            else:
                hasInitExession = False

        if not hasInitExession:
            link_nodes(node, node_startLoop)
        node_condition = node_startLoop

        if hasCondition:
            if hasInitExession and len(children) >= 2:
                candidate = children[1]
            else:
                candidate = children[0]
            if candidate['name'] not in ['VariableDefinitionStatement',
                                         'VariableDeclarationStatement',
                                         'ExpressionStatement']:
                node_condition = self._new_node(NodeType.IFLOOP)
                #expression = parse_expression(candidate, self)
                expression = candidate
                node_condition.add_unparsed_expression(expression)
                link_nodes(node_startLoop, node_condition)
                link_nodes(node_condition, node_endLoop)
                hasCondition = True
            else:
                hasCondition = False


        node_statement = self._parse_statement(children[-1], node_condition)

        node_LoopExpression = node_statement
        if hasLoopExpression:
            if len(children) > 2:
                if children[-2]['name'] == 'ExpressionStatement':
                    node_LoopExpression = self._parse_statement(children[-2], node_statement)

        link_nodes(node_LoopExpression, node_startLoop)

        return node_endLoop

    def _parse_dowhile(self, doWhilestatement, node):
        children = doWhilestatement['children']

        node_startDoWhile = self._new_node(NodeType.STARTLOOP)

        # same order in the AST as while
        node_condition = self._new_node(NodeType.IFLOOP)
        #expression = parse_expression(children[0], self)
        expression = children[0]
        node_condition.add_unparsed_expression(expression)

        statement = self._parse_statement(children[1], node_condition)
        node_endDoWhile = self._new_node(NodeType.ENDLOOP)

        link_nodes(node, node_startDoWhile)
        link_nodes(node_startDoWhile, node_condition)
        link_nodes(statement, node_condition)
        link_nodes(node_condition, node_endDoWhile)

        return node_endDoWhile

    def _parse_variable_definition(self, statement, node):
        #assert len(statement['children']) == 1
        # if there is, parse default value
        #assert not 'attributes' in statement 

        try:
            local_var = LocalVariableSolc(statement)
            #local_var = LocalVariableSolc(statement['children'][0], statement['children'][1::])
            local_var.set_function(self)
            local_var.set_offset(statement['src'], self.contract.slither)

            self._variables[local_var.name] = local_var
            #local_var.analyze(self)

            new_node = self._new_node(NodeType.VARIABLE)
            new_node.add_variable_declaration(local_var)
            link_nodes(node, new_node)
            return new_node
        except MultipleVariablesDeclaration:
            # Custom handling of var (a,b) = .. style declaration
            count = 0
            children = statement['children']
            child = children[0]
            while child['name'] == 'VariableDeclaration':
                count = count +1
                child = children[count]

            assert len(children) == (count + 1)
            tuple_vars = children[count]


            variables_declaration = children[0:count]
            i = 0
            new_node = node
            if tuple_vars['name'] == 'TupleExpression':
                assert len(tuple_vars['children']) == count
                for variable in variables_declaration:
                    init = tuple_vars['children'][i]
                    src = variable['src']
                    i= i+1
                    # Create a fake statement to be consistent
                    new_statement = {'name':'VariableDefinitionStatement',
                                     'src': src,
                                     'children':[variable, init]}

                    new_node = self._parse_variable_definition(new_statement, new_node)
            else:
                # If we have
                # var (a, b) = f()
                # we can split in multiple declarations, without init
                # Then we craft one expression that does not assignment
                assert tuple_vars['name'] in ['FunctionCall', 'Conditional']
                variables = []
                for variable in variables_declaration:
                    src = variable['src']
                    i= i+1
                    # Create a fake statement to be consistent
                    new_statement = {'name':'VariableDefinitionStatement',
                                     'src': src,
                                     'children':[variable]}
                    variables.append(variable)

                    new_node = self._parse_variable_definition_init_tuple(new_statement, i, new_node)
                var_identifiers = []
                # craft of the expression doing the assignement
                for v in variables:
                    identifier = {
                        'name' : 'Identifier',
                        'src': v['src'],
                        'attributes': {
                                'value': v['attributes']['name'],
                                'type': v['attributes']['type']}
                    }
                    var_identifiers.append(identifier)

                expression = {
                    'name' : 'Assignment',
                    'src':statement['src'],
                    'attributes': {'operator': '=',
                                   'type':'tuple()'},
                    'children':
                    [{'name': 'TupleExpression',
                      'src': statement['src'],
                      'children': var_identifiers},
                     tuple_vars]}
                node = new_node
                new_node = self._new_node(NodeType.EXPRESSION)
                new_node.add_unparsed_expression(expression)
                link_nodes(node, new_node)


            return new_node

    def _parse_variable_definition_init_tuple(self, statement, index, node):
        local_var = LocalVariableInitFromTupleSolc(statement, index)
        #local_var = LocalVariableSolc(statement['children'][0], statement['children'][1::])
        local_var.set_function(self)
        local_var.set_offset(statement['src'], self.contract.slither)

        self._variables[local_var.name] = local_var
#        local_var.analyze(self)

        new_node = self._new_node(NodeType.VARIABLE)
        new_node.add_variable_declaration(local_var)
        link_nodes(node, new_node)
        return new_node


    def _parse_statement(self, statement, node):
        """

        Return:
            node
        """
        # Statement = IfStatement | WhileStatement | ForStatement | Block | InlineAssemblyStatement |
        #            ( DoWhileStatement | PlaceholderStatement | Continue | Break | Return |
        #                          Throw | EmitStatement | SimpleStatement ) ';'
        # SimpleStatement = VariableDefinition | ExpressionStatement

        name = statement['name']
        # SimpleStatement = VariableDefinition | ExpressionStatement
        if name == 'IfStatement':
            node = self._parse_if(statement, node)
        elif name == 'WhileStatement':
            node = self._parse_while(statement, node)
        elif name == 'ForStatement':
            node = self._parse_for(statement, node)
        elif name == 'Block':
            node = self._parse_block(statement, node)
        elif name == 'InlineAssembly':
            break_node = self._new_node(NodeType.ASSEMBLY)
            link_nodes(node, break_node)
            node = break_node
        elif name == 'DoWhileStatement':
            node = self._parse_dowhile(statement, node)
        # For Continue / Break / Return / Throw
        # The is fixed later
        elif name == 'Continue':
            continue_node = self._new_node(NodeType.CONTINUE)
            link_nodes(node, continue_node)
            node = continue_node
        elif name == 'Break':
            break_node = self._new_node(NodeType.BREAK)
            link_nodes(node, break_node)
            node = break_node
        elif name == 'Return':
            return_node = self._new_node(NodeType.RETURN)
            link_nodes(node, return_node)
            if 'children' in statement and statement['children']:
                assert len(statement['children']) == 1
                expression = statement['children'][0]
                return_node.add_unparsed_expression(expression)
            node = return_node
        elif name == 'Throw':
            throw_node = self._new_node(NodeType.THROW)
            link_nodes(node, throw_node)
            node = throw_node
        elif name == 'EmitStatement':
            #expression = parse_expression(statement['children'][0], self)
            expression = statement['children'][0]
            new_node = self._new_node(NodeType.EXPRESSION)
            new_node.add_unparsed_expression(expression)
            link_nodes(node, new_node)
            node = new_node
        elif name in ['VariableDefinitionStatement', 'VariableDeclarationStatement']:
            node = self._parse_variable_definition(statement, node)
        elif name == 'ExpressionStatement':
            assert len(statement['children']) == 1
            assert not 'attributes' in statement
            #expression = parse_expression(statement['children'][0], self)
            expression = statement['children'][0]
            new_node = self._new_node(NodeType.EXPRESSION)
            new_node.add_unparsed_expression(expression)
            link_nodes(node, new_node)
            node = new_node
        else:
            logger.error('Statement not parsed %s'%name)
            exit(-1)

        return node

    def _parse_block(self, block, node):
        '''
        Return:
            Node
        '''
        assert block['name'] == 'Block'

        for child in block['children']:
            node = self._parse_statement(child, node)
        return node

    def _parse_cfg(self, cfg):

        assert cfg['name'] == 'Block'

        node = self._new_node(NodeType.ENTRYPOINT)
        self._entry_point = node

        if not cfg['children']:
            self._is_empty = True
        else:
            self._is_empty = False
            self._parse_block(cfg, node)
            self._remove_incorrect_edges()
            self._remove_alone_endif()

    def _find_end_loop(self, node, visited):
        if node in visited:
            return None

        if node.type == NodeType.ENDLOOP:
            return node

        visited = visited + [node]
        for son in node.sons:
            ret = self._find_end_loop(son, visited)
            if ret:
                return ret

        return None

    def _find_start_loop(self, node, visited):
        if node in visited:
            return None

        if node.type == NodeType.STARTLOOP:
            return node

        visited = visited + [node]
        for father in node.fathers:
            ret = self._find_start_loop(father, visited)
            if ret:
                return ret

        return None

    def _fix_break_node(self, node):
        end_node = self._find_end_loop(node, [])

        if not end_node:
            logger.error('Break in no-loop context {}'.format(node.nodeId()))
            exit(-1)

        for son in node.sons:
            son.remove_father(node)
        node.set_sons([end_node])
        end_node.add_father(node)

    def _fix_continue_node(self, node):
        start_node = self._find_start_loop(node, [])

        if not start_node:
            logger.error('Continue in no-loop context {}'.format(node.nodeId()))
            exit(-1)

        for son in node.sons:
            son.remove_father(node)
        node.set_sons([start_node])
        start_node.add_father(node)

    def _remove_incorrect_edges(self):
        for node in self._nodes:
            if node.type in [NodeType.RETURN, NodeType.THROW]:
                for son in node.sons:
                    son.remove_father(node)
                node.set_sons([])
            if node.type in [NodeType.BREAK]:
                self._fix_break_node(node)
            if node.type in [NodeType.CONTINUE]:
                self._fix_continue_node(node)

    def _remove_alone_endif(self):
        """
            Can occur on:
            if(..){
                return
            }
            else{
                return
            }

        """
        self._nodes = [n for n in self.nodes if n.type != NodeType.ENDIF or n.sons or n.fathers]

    def _parse_params(self, params):

        assert params['name'] == 'ParameterList'
        for param in params['children']:
            assert param['name'] == 'VariableDeclaration'

            local_var = LocalVariableSolc(param)

            local_var.set_function(self)
            local_var.set_offset(param['src'], self.contract.slither)
            local_var.analyze(self)

            # see https://solidity.readthedocs.io/en/v0.4.24/types.html?highlight=storage%20location#data-location
            if local_var.location == 'default':
                local_var.set_location('memory')

            self._variables[local_var.name] = local_var
            self._parameters.append(local_var)

    def _parse_returns(self, returns):

        assert returns['name'] == 'ParameterList'
        for ret in returns['children']:
            assert ret['name'] == 'VariableDeclaration'

            local_var = LocalVariableSolc(ret)

            local_var.set_function(self)
            local_var.set_offset(ret['src'], self.contract.slither)
            local_var.analyze(self)

            # see https://solidity.readthedocs.io/en/v0.4.24/types.html?highlight=storage%20location#data-location
            if local_var.location == 'default':
                local_var.set_location('memory')

            self._variables[local_var.name] = local_var
            self._returns.append(local_var)


    def _parse_modifier(self, modifier):
        m = parse_expression(modifier, self)
        self._expression_modifiers.append(m)
        self._modifiers += [m for m in ExportValues(m).result() if isinstance(m, Function)]


    def analyze_params(self):
        # Can be re-analyzed due to inheritance
        if self._params_was_analyzed:
            return

        self._params_was_analyzed = True

        self._analyze_attributes()

        children = self._functionNotParsed['children']

        params = children[0]
        returns = children[1]

        if params:
            self._parse_params(params)
        if returns:
            self._parse_returns(returns)

    def analyze_content(self):
        if self._content_was_analyzed:
            return

        self._content_was_analyzed = True

        children = self._functionNotParsed['children']
        self._is_implemented = False
        for child in children[2:]:
            if child['name'] == 'Block':
                self._is_implemented = True
                self._parse_cfg(child)
                continue

            assert child['name'] == 'ModifierInvocation'

            self._parse_modifier(child)

        for local_vars in self.variables:
            local_vars.analyze(self)

        for node in self.nodes:
            node.analyze_expressions(self)

        ternary_found = True
        while ternary_found:
            ternary_found = False
            for node in self.nodes:
                has_cond = HasConditional(node.expression)
                if has_cond.result():
                    st = SplitTernaryExpression(node.expression)
                    condition = st.condition
                    assert condition
                    true_expr = st.true_expression
                    false_expr = st.false_expression
                    self.split_ternary_node(node, condition, true_expr, false_expr)
                    ternary_found = True
                    break
        self._remove_alone_endif()

        self._analyze_read_write()
        self._analyze_calls()
        for node in self.nodes:
            node.slithir_generation()
 

    def split_ternary_node(self, node, condition, true_expr, false_expr):
        condition_node = self._new_node(NodeType.IF)
        condition_node.add_expression(condition)
        condition_node.analyze_expressions(self)

        true_node = self._new_node(node.type)
        if node.type == NodeType.VARIABLE:
            true_node.add_variable_declaration(node.variable_declaration)
        true_node.add_expression(true_expr)
        true_node.analyze_expressions(self)

        false_node = self._new_node(node.type)
        if node.type == NodeType.VARIABLE:
            false_node.add_variable_declaration(node.variable_declaration)
        false_node.add_expression(false_expr)
        false_node.analyze_expressions(self)

        endif_node = self._new_node(NodeType.ENDIF)

        for father in node.fathers:
            father.remove_son(node)
            father.add_son(condition_node)
            condition_node.add_father(father)

        for son in node.sons:
            son.remove_father(node)
            son.add_father(endif_node)
            endif_node.add_son(son)

        link_nodes(condition_node, true_node)
        link_nodes(condition_node, false_node)


        if not true_node.type in [NodeType.THROW, NodeType.RETURN]:
            link_nodes(true_node, endif_node)
        if not false_node.type in [NodeType.THROW, NodeType.RETURN]:
            link_nodes(false_node, endif_node)

        self._nodes = [n for n in self._nodes if n.node_id != node.node_id]


