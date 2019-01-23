"""
    Event module
"""
import logging

from slither.core.cfg.node import NodeType, link_nodes
from slither.core.declarations.function import Function
from slither.core.dominators.utils import (compute_dominance_frontier,
                                           compute_dominators)
from slither.core.expressions import AssignmentOperation
from slither.core.variables.state_variable import StateVariable
from slither.slithir.operations import (Assignment, HighLevelCall,
                                        InternalCall, InternalDynamicCall,
                                        LowLevelCall, OperationWithLValue, Phi,
                                        PhiCallback, LibraryCall)
from slither.slithir.utils.ssa import add_ssa_ir, transform_slithir_vars_to_ssa
from slither.slithir.variables import LocalIRVariable, ReferenceVariable
from slither.solc_parsing.cfg.node import NodeSolc
from slither.solc_parsing.expressions.expression_parsing import \
    parse_expression
from slither.solc_parsing.variables.local_variable import LocalVariableSolc
from slither.solc_parsing.variables.local_variable_init_from_tuple import \
    LocalVariableInitFromTupleSolc
from slither.solc_parsing.variables.variable_declaration import \
    MultipleVariablesDeclaration
from slither.utils.expression_manipulations import SplitTernaryExpression
from slither.visitors.expression.export_values import ExportValues
from slither.visitors.expression.has_conditional import HasConditional
from slither.core.declarations.contract import Contract

logger = logging.getLogger("FunctionSolc")

class FunctionSolc(Function):
    """
    Event class
    """
    # elems = [(type, name)]

    def __init__(self, function, contract):
        super(FunctionSolc, self).__init__()
        self._contract = contract
        if self.is_compact_ast:
            self._name = function['name']
        else:
            self._name = function['attributes'][self.get_key()]
        self._functionNotParsed = function
        self._params_was_analyzed = False
        self._content_was_analyzed = False
        self._counter_nodes = 0

    def get_key(self):
        return self.slither.get_key()

    def get_children(self, key):
        if self.is_compact_ast:
            return key
        return 'children'

    @property
    def is_compact_ast(self):
        return self.slither.is_compact_ast

    def _analyze_attributes(self):
        if self.is_compact_ast:
            attributes = self._functionNotParsed
        else:
            attributes = self._functionNotParsed['attributes']

        if 'payable' in attributes:
            self._payable = attributes['payable']
        if 'stateMutability' in attributes:
            if attributes['stateMutability'] == 'payable':
                self._payable = True
            elif attributes['stateMutability'] == 'pure':
                self._pure = True
                self._view = True
            elif attributes['stateMutability'] == 'view':
                self._view = True

        if 'constant' in attributes:
            self._view = attributes['constant']

        self._is_constructor = False

        if 'isConstructor' in attributes:
            self._is_constructor = attributes['isConstructor']

        if 'kind' in attributes:
            if attributes['kind'] == 'constructor':
                self._is_constructor = True

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

    def _new_node(self, node_type, src):
        node = NodeSolc(node_type, self._counter_nodes)
        node.set_offset(src, self.slither)
        self._counter_nodes += 1
        node.set_function(self)
        self._nodes.append(node)
        return node

    def _parse_if(self, ifStatement, node):
        # IfStatement = 'if' '(' Expression ')' Statement ( 'else' Statement )?
        falseStatement = None

        if self.is_compact_ast:
            condition = ifStatement['condition']
            # Note: check if the expression could be directly
            # parsed here
            condition_node = self._new_node(NodeType.IF, ifStatement['src'])
            condition_node.add_unparsed_expression(condition)
            link_nodes(node, condition_node)
            trueStatement = self._parse_statement(ifStatement['trueBody'], condition_node)
            if ifStatement['falseBody']:
                falseStatement = self._parse_statement(ifStatement['falseBody'], condition_node)
        else:
            children = ifStatement[self.get_children('children')]
            condition = children[0]
            # Note: check if the expression could be directly
            # parsed here
            condition_node = self._new_node(NodeType.IF, ifStatement['src'])
            condition_node.add_unparsed_expression(condition)
            link_nodes(node, condition_node)
            trueStatement = self._parse_statement(children[1], condition_node)
            if len(children) == 3:
                falseStatement = self._parse_statement(children[2], condition_node)

        endIf_node = self._new_node(NodeType.ENDIF, ifStatement['src'])
        link_nodes(trueStatement, endIf_node)

        if falseStatement:
            link_nodes(falseStatement, endIf_node)
        else:
            link_nodes(condition_node, endIf_node)
        return endIf_node

    def _parse_while(self, whileStatement, node):
        # WhileStatement = 'while' '(' Expression ')' Statement

        node_startWhile = self._new_node(NodeType.STARTLOOP, whileStatement['src'])
        node_condition = self._new_node(NodeType.IFLOOP, whileStatement['src'])

        if self.is_compact_ast:
            node_condition.add_unparsed_expression(whileStatement['condition'])
            statement = self._parse_statement(whileStatement['body'], node_condition)
        else:
            children = whileStatement[self.get_children('children')]
            expression = children[0]
            node_condition.add_unparsed_expression(expression)
            statement = self._parse_statement(children[1], node_condition)

        node_endWhile = self._new_node(NodeType.ENDLOOP, whileStatement['src'])

        link_nodes(node, node_startWhile)
        link_nodes(node_startWhile, node_condition)
        link_nodes(statement, node_condition)
        link_nodes(node_condition, node_endWhile)

        return node_endWhile

    def _parse_for_compact_ast(self, statement, node):
        body = statement['body']
        init_expression = statement['initializationExpression']
        condition = statement['condition']
        loop_expression = statement['loopExpression']

        node_startLoop = self._new_node(NodeType.STARTLOOP, statement['src'])
        node_endLoop = self._new_node(NodeType.ENDLOOP, statement['src'])

        if init_expression:
            node_init_expression = self._parse_statement(init_expression, node)
            link_nodes(node_init_expression, node_startLoop)
        else:
            link_nodes(node, node_startLoop)

        if condition:
            node_condition = self._new_node(NodeType.IFLOOP, statement['src'])
            node_condition.add_unparsed_expression(condition)
            link_nodes(node_startLoop, node_condition)
            link_nodes(node_condition, node_endLoop)
        else:
            node_condition = node_startLoop

        node_body = self._parse_statement(body, node_condition)

        if loop_expression:
            node_LoopExpression = self._parse_statement(loop_expression, node_body)
            link_nodes(node_LoopExpression, node_condition)
        else:
            link_nodes(node_body, node_condition)

        if not condition:
            if not loop_expression:
                # TODO: fix case where loop has no expression
                link_nodes(node_startLoop, node_endLoop)
            else:
                link_nodes(node_LoopExpression, node_endLoop)

        return node_endLoop


    def _parse_for(self, statement, node):
        # ForStatement = 'for' '(' (SimpleStatement)? ';' (Expression)? ';' (ExpressionStatement)? ')' Statement

        # the handling of loop in the legacy ast is too complex
        # to integrate the comapct ast
        # its cleaner to do it separately
        if self.is_compact_ast:
            return self._parse_for_compact_ast(statement, node)

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


        node_startLoop = self._new_node(NodeType.STARTLOOP, statement['src'])
        node_endLoop = self._new_node(NodeType.ENDLOOP, statement['src'])

        children = statement[self.get_children('children')]

        if hasInitExession:
            if len(children) >= 2:
                if children[0][self.get_key()] in ['VariableDefinitionStatement',
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
            if candidate[self.get_key()] not in ['VariableDefinitionStatement',
                                         'VariableDeclarationStatement',
                                         'ExpressionStatement']:
                node_condition = self._new_node(NodeType.IFLOOP, statement['src'])
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
                if children[-2][self.get_key()] == 'ExpressionStatement':
                    node_LoopExpression = self._parse_statement(children[-2], node_statement)
            if not hasCondition:
                link_nodes(node_LoopExpression, node_endLoop)

        if not hasCondition and not hasLoopExpression:
            link_nodes(node, node_endLoop)

        link_nodes(node_LoopExpression, node_condition)

        return node_endLoop

    def _parse_dowhile(self, doWhilestatement, node):

        node_startDoWhile = self._new_node(NodeType.STARTLOOP, doWhilestatement['src'])
        node_condition = self._new_node(NodeType.IFLOOP, doWhilestatement['src'])

        if self.is_compact_ast:
            node_condition.add_unparsed_expression(doWhilestatement['condition'])
            statement = self._parse_statement(doWhilestatement['body'], node_condition)
        else:
            children = doWhilestatement[self.get_children('children')]
            # same order in the AST as while
            expression = children[0]
            node_condition.add_unparsed_expression(expression)
            statement = self._parse_statement(children[1], node_condition)

        node_endDoWhile = self._new_node(NodeType.ENDLOOP, doWhilestatement['src'])

        link_nodes(node, node_startDoWhile)
        link_nodes(node_startDoWhile, node_condition.sons[0])
        link_nodes(statement, node_condition)
        link_nodes(node_condition, node_endDoWhile)
        return node_endDoWhile

    def _parse_variable_definition(self, statement, node):
        try:
            local_var = LocalVariableSolc(statement)
            local_var.set_function(self)
            local_var.set_offset(statement['src'], self.contract.slither)

            self._variables[local_var.name] = local_var
            #local_var.analyze(self)

            new_node = self._new_node(NodeType.VARIABLE, statement['src'])
            new_node.add_variable_declaration(local_var)
            link_nodes(node, new_node)
            return new_node
        except MultipleVariablesDeclaration:
            # Custom handling of var (a,b) = .. style declaration
            if self.is_compact_ast:
                variables = statement['declarations']
                count = len(variables)

                if statement['initialValue']['nodeType'] == 'TupleExpression':
                    inits = statement['initialValue']['components']
                    i = 0
                    new_node = node
                    for variable in variables:
                        init = inits[i]
                        src = variable['src']
                        i = i+1

                        new_statement = {'nodeType':'VariableDefinitionStatement',
                                         'src': src,
                                         'declarations':[variable],
                                         'initialValue':init}
                        new_node = self._parse_variable_definition(new_statement, new_node)

                else:
                    # If we have
                    # var (a, b) = f()
                    # we can split in multiple declarations, without init
                    # Then we craft one expression that does the assignment                   
                    variables = []
                    i = 0
                    new_node = node
                    for variable in statement['declarations']:
                        i = i+1
                        if variable:
                            src = variable['src']
                            # Create a fake statement to be consistent
                            new_statement = {'nodeType':'VariableDefinitionStatement',
                                             'src': src,
                                             'declarations':[variable]}
                            variables.append(variable)

                            new_node = self._parse_variable_definition_init_tuple(new_statement,
                                                                                  i,
                                                                                  new_node)

                    var_identifiers = []
                    # craft of the expression doing the assignement
                    for v in variables:
                        identifier = {
                            'nodeType':'Identifier',
                            'src': v['src'],
                            'name': v['name'],
                            'typeDescriptions': {
                                'typeString':v['typeDescriptions']['typeString']
                            }
                        }
                        var_identifiers.append(identifier)

                    tuple_expression = {'nodeType':'TupleExpression',
                                        'src': statement['src'],
                                        'components':var_identifiers}

                    expression = {
                        'nodeType' : 'Assignment',
                        'src':statement['src'],
                        'operator': '=',
                        'type':'tuple()',
                        'leftHandSide': tuple_expression,
                        'rightHandSide': statement['initialValue'],
                        'typeDescriptions': {'typeString':'tuple()'}
                        }
                    node = new_node
                    new_node = self._new_node(NodeType.EXPRESSION, statement['src'])
                    new_node.add_unparsed_expression(expression)
                    link_nodes(node, new_node)


            else:
                count = 0
                children = statement[self.get_children('children')]
                child = children[0]
                while child[self.get_key()] == 'VariableDeclaration':
                    count = count +1
                    child = children[count]

                assert len(children) == (count + 1)
                tuple_vars = children[count]


                variables_declaration = children[0:count]
                i = 0
                new_node = node
                if tuple_vars[self.get_key()] == 'TupleExpression':
                    assert len(tuple_vars[self.get_children('children')]) == count
                    for variable in variables_declaration:
                        init = tuple_vars[self.get_children('children')][i]
                        src = variable['src']
                        i = i+1
                        # Create a fake statement to be consistent
                        new_statement = {self.get_key():'VariableDefinitionStatement',
                                         'src': src,
                                         self.get_children('children'):[variable, init]}

                        new_node = self._parse_variable_definition(new_statement, new_node)
                else:
                    # If we have
                    # var (a, b) = f()
                    # we can split in multiple declarations, without init
                    # Then we craft one expression that does the assignment
                    assert tuple_vars[self.get_key()] in ['FunctionCall', 'Conditional']
                    variables = []
                    for variable in variables_declaration:
                        src = variable['src']
                        i = i+1
                        # Create a fake statement to be consistent
                        new_statement = {self.get_key():'VariableDefinitionStatement',
                                         'src': src,
                                         self.get_children('children'):[variable]}
                        variables.append(variable)

                        new_node = self._parse_variable_definition_init_tuple(new_statement, i, new_node)
                    var_identifiers = []
                    # craft of the expression doing the assignement
                    for v in variables:
                        identifier = {
                            self.get_key() : 'Identifier',
                            'src': v['src'],
                            'attributes': {
                                    'value': v['attributes'][self.get_key()],
                                    'type': v['attributes']['type']}
                        }
                        var_identifiers.append(identifier)

                    expression = {
                        self.get_key() : 'Assignment',
                        'src':statement['src'],
                        'attributes': {'operator': '=',
                                       'type':'tuple()'},
                        self.get_children('children'):
                        [{self.get_key(): 'TupleExpression',
                          'src': statement['src'],
                          self.get_children('children'): var_identifiers},
                         tuple_vars]}
                    node = new_node
                    new_node = self._new_node(NodeType.EXPRESSION, statement['src'])
                    new_node.add_unparsed_expression(expression)
                    link_nodes(node, new_node)


            return new_node

    def _parse_variable_definition_init_tuple(self, statement, index, node):
        local_var = LocalVariableInitFromTupleSolc(statement, index)
        #local_var = LocalVariableSolc(statement[self.get_children('children')][0], statement[self.get_children('children')][1::])
        local_var.set_function(self)
        local_var.set_offset(statement['src'], self.contract.slither)

        self._variables[local_var.name] = local_var
#        local_var.analyze(self)

        new_node = self._new_node(NodeType.VARIABLE, statement['src'])
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

        name = statement[self.get_key()]
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
            break_node = self._new_node(NodeType.ASSEMBLY, statement['src'])
            self._contains_assembly = True
            link_nodes(node, break_node)
            node = break_node
        elif name == 'DoWhileStatement':
            node = self._parse_dowhile(statement, node)
        # For Continue / Break / Return / Throw
        # The is fixed later
        elif name == 'Continue':
            continue_node = self._new_node(NodeType.CONTINUE, statement['src'])
            link_nodes(node, continue_node)
            node = continue_node
        elif name == 'Break':
            break_node = self._new_node(NodeType.BREAK, statement['src'])
            link_nodes(node, break_node)
            node = break_node
        elif name == 'Return':
            return_node = self._new_node(NodeType.RETURN, statement['src'])
            link_nodes(node, return_node)
            if self.is_compact_ast:
                if statement['expression']:
                    return_node.add_unparsed_expression(statement['expression'])
            else:
                if self.get_children('children') in statement and statement[self.get_children('children')]:
                    assert len(statement[self.get_children('children')]) == 1
                    expression = statement[self.get_children('children')][0]
                    return_node.add_unparsed_expression(expression)
            node = return_node
        elif name == 'Throw':
            throw_node = self._new_node(NodeType.THROW, statement['src'])
            link_nodes(node, throw_node)
            node = throw_node
        elif name == 'EmitStatement':
            #expression = parse_expression(statement[self.get_children('children')][0], self)
            if self.is_compact_ast:
                expression = statement['eventCall']
            else:
                expression = statement[self.get_children('children')][0]
            new_node = self._new_node(NodeType.EXPRESSION, statement['src'])
            new_node.add_unparsed_expression(expression)
            link_nodes(node, new_node)
            node = new_node
        elif name in ['VariableDefinitionStatement', 'VariableDeclarationStatement']:
            node = self._parse_variable_definition(statement, node)
        elif name == 'ExpressionStatement':
            #assert len(statement[self.get_children('expression')]) == 1
            #assert not 'attributes' in statement
            #expression = parse_expression(statement[self.get_children('children')][0], self)
            if self.is_compact_ast:
                expression = statement[self.get_children('expression')]
            else:
                expression = statement[self.get_children('expression')][0]
            new_node = self._new_node(NodeType.EXPRESSION, statement['src'])
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
        assert block[self.get_key()] == 'Block'

        if self.is_compact_ast:
            statements = block['statements']
        else:
            statements = block[self.get_children('children')]

        for statement in statements:
            node = self._parse_statement(statement, node)
        return node

    def _parse_cfg(self, cfg):

        assert cfg[self.get_key()] == 'Block'

        node = self._new_node(NodeType.ENTRYPOINT, cfg['src'])
        self._entry_point = node

        if self.is_compact_ast:
            statements = cfg['statements']
        else:
            statements = cfg[self.get_children('children')]

        if not statements:
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

        # nested loop
        if node.type == NodeType.STARTLOOP:
            return None

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
            logger.error('Break in no-loop context {}'.format(node))
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

            Iterate until a fix point to remove the ENDIF node
            creates on the following pattern
            if(){
                return
            }
            else if(){
                return
            }
        """
        prev_nodes = []
        while set(prev_nodes) != set(self.nodes):
            prev_nodes = self.nodes
            to_remove = []
            for node in self.nodes:
                if node.type == NodeType.ENDIF and not node.fathers:
                    for son in node.sons:
                        son.remove_father(node)
                    node.set_sons([])
                    to_remove.append(node)
            self._nodes = [n for n in self.nodes if not n in to_remove]
#
    def _parse_params(self, params):
        assert params[self.get_key()] == 'ParameterList'

        if self.is_compact_ast:
            params = params['parameters']
        else:
            params = params[self.get_children('children')]

        for param in params:
            assert param[self.get_key()] == 'VariableDeclaration'

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

        assert returns[self.get_key()] == 'ParameterList'

        if self.is_compact_ast:
            returns = returns['parameters']
        else:
            returns = returns[self.get_children('children')]

        for ret in returns:
            assert ret[self.get_key()] == 'VariableDeclaration'

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
        for m in ExportValues(m).result():
            if isinstance(m, Function):
                self._modifiers.append(m)
            elif isinstance(m, Contract):
                self._explicit_base_constructor_calls.append(m)


    def analyze_params(self):
        # Can be re-analyzed due to inheritance
        if self._params_was_analyzed:
            return

        self._params_was_analyzed = True

        self._analyze_attributes()

        if self.is_compact_ast:
            params = self._functionNotParsed['parameters']
            returns = self._functionNotParsed['returnParameters']
        else:
            children = self._functionNotParsed[self.get_children('children')]
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

        if self.is_compact_ast:
            body = self._functionNotParsed['body']

            if body and body[self.get_key()] == 'Block':
                self._is_implemented = True
                self._parse_cfg(body)

            for modifier in self._functionNotParsed['modifiers']:
                self._parse_modifier(modifier)

        else:
            children = self._functionNotParsed[self.get_children('children')]
            self._is_implemented = False
            for child in children[2:]:
                if child[self.get_key()] == 'Block':
                    self._is_implemented = True
                    self._parse_cfg(child)
    
            # Parse modifier after parsing all the block
            # In the case a local variable is used in the modifier
            for child in children[2:]:
                if child[self.get_key()] == 'ModifierInvocation':
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

    def get_last_ssa_state_variables_instances(self):
        if not self.is_implemented:
            return dict()

        # node, values 
        to_explore = [(self._entry_point, dict())]
        # node -> values
        explored = dict()
        # name -> instances
        ret = dict()

        while to_explore:
            node, values = to_explore[0]
            to_explore = to_explore[1::]

            if node.type != NodeType.ENTRYPOINT:
                for ir_ssa in node.irs_ssa:
                    if isinstance(ir_ssa, OperationWithLValue):
                        lvalue = ir_ssa.lvalue
                        if isinstance(lvalue, ReferenceVariable):
                            lvalue = lvalue.points_to_origin
                        if isinstance(lvalue, StateVariable):
                            values[lvalue.canonical_name] = {lvalue}

            # Check for fixpoint
            if node in explored:
                if values == explored[node]:
                    continue
                for k, instances in values.items():
                    if not k in explored[node]:
                        explored[node][k] = set()
                    explored[node][k] |= instances
                values = explored[node]
            else:
                explored[node] = values

            # Return condition
            if not node.sons and node.type != NodeType.THROW:
                for name, instances in values.items():
                    if name not in ret:
                        ret[name] = set()
                    ret[name] |= instances

            for son in node.sons:
                to_explore.append((son, dict(values)))

        return ret

    @staticmethod
    def _unchange_phi(ir):
        if not isinstance(ir, (Phi, PhiCallback)) or len(ir.rvalues) > 1:
            return False
        if not ir.rvalues:
            return True
        return ir.rvalues[0] == ir.lvalue

    def fix_phi(self, last_state_variables_instances, initial_state_variables_instances):
        for node in self.nodes:
            for ir in node.irs_ssa:
                if node == self.entry_point:
                    additional = [initial_state_variables_instances[ir.lvalue.canonical_name]]
                    additional += last_state_variables_instances[ir.lvalue.canonical_name]
                    ir.rvalues = list(set(additional + ir.rvalues))
                if isinstance(ir, PhiCallback):
                    callee_ir = ir.callee_ir
                    if isinstance(callee_ir, InternalCall):
                        last_ssa = callee_ir.function.get_last_ssa_state_variables_instances()
                        if ir.lvalue.canonical_name in last_ssa:
                            ir.rvalues = list(last_ssa[ir.lvalue.canonical_name])
                        else:
                            ir.rvalues = [ir.lvalue]
                    else:
                        additional = last_state_variables_instances[ir.lvalue.canonical_name]
                        ir.rvalues = list(set(additional + ir.rvalues))

            node.irs_ssa = [ir for ir in node.irs_ssa if not self._unchange_phi(ir)]

    def generate_slithir_and_analyze(self):
        for node in self.nodes:
            node.slithir_generation()
        self._analyze_read_write()
        self._analyze_calls()

    def generate_slithir_ssa(self, all_ssa_state_variables_instances):
        compute_dominators(self.nodes)
        compute_dominance_frontier(self.nodes)
        transform_slithir_vars_to_ssa(self)
        add_ssa_ir(self, all_ssa_state_variables_instances)

    def update_read_write_using_ssa(self):
        for node in self.nodes:
            node.update_read_write_using_ssa()
        self._analyze_read_write()

    def split_ternary_node(self, node, condition, true_expr, false_expr):
        condition_node = self._new_node(NodeType.IF, node.source_mapping)
        condition_node.add_expression(condition)
        condition_node.analyze_expressions(self)

        if node.type == NodeType.VARIABLE:
            condition_node.add_variable_declaration(node.variable_declaration)

        true_node = self._new_node(NodeType.EXPRESSION, node.source_mapping)
        if node.type == NodeType.VARIABLE:
            assert isinstance(true_expr, AssignmentOperation)
            #true_expr = true_expr.expression_right
        elif node.type == NodeType.RETURN:
            true_node.type = NodeType.RETURN
        true_node.add_expression(true_expr)
        true_node.analyze_expressions(self)

        false_node = self._new_node(NodeType.EXPRESSION, node.source_mapping)
        if node.type == NodeType.VARIABLE:
            assert isinstance(false_expr, AssignmentOperation)
        elif node.type == NodeType.RETURN:
            false_node.type = NodeType.RETURN
            #false_expr = false_expr.expression_right
        false_node.add_expression(false_expr)
        false_node.analyze_expressions(self)

        endif_node = self._new_node(NodeType.ENDIF, node.source_mapping)

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


