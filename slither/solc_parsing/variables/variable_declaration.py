import logging
from slither.solc_parsing.expressions.expression_parsing import parse_expression

from slither.core.variables.variable import Variable

from slither.solc_parsing.solidity_types.type_parsing import parse_type, UnknownType

from slither.core.solidity_types.elementary_type import ElementaryType, NonElementaryType

logger = logging.getLogger("VariableDeclarationSolcParsing")

class MultipleVariablesDeclaration(Exception):
    '''
    This is raised on
    var (a,b) = ...
    It should occur only on local variable definition
    '''
    pass

class VariableDeclarationSolc(Variable):

    def __init__(self, var):
        '''
            A variable can be declared through a statement, or directly.
            If it is through a statement, the following children may contain
            the init value.
            It may be possible that the variable is declared through a statement,
            but the init value is declared at the VariableDeclaration children level
        '''

        super(VariableDeclarationSolc, self).__init__()
        self._was_analyzed = False
        self._elem_to_parse = None
        self._initializedNotParsed = None

        if var['name'] in ['VariableDeclarationStatement', 'VariableDefinitionStatement']:
            if len(var['children']) == 2:
                init = var['children'][1]
            elif len(var['children']) == 1:
                init = None
            elif len(var['children']) > 2:
                raise MultipleVariablesDeclaration
            else:
                logger.error('Variable declaration without children?'+var)
                exit(-1)
            declaration = var['children'][0]
            self._init_from_declaration(declaration, init)
        elif  var['name'] == 'VariableDeclaration':
            self._init_from_declaration(var, None)
        else:
            logger.error('Incorrect variable declaration type {}'.format(var['name']))
            exit(-1)

    @property
    def initialized(self):
        return self._initialized

    @property
    def uninitialized(self):
        return not self._initialized

    def _analyze_variable_attributes(self, attributes):
        if 'visibility' in attributes:
            self._visibility = attributes['visibility']
        else:
            self._visibility = 'internal'

    def _init_from_declaration(self, var, init):
        assert len(var['children']) <= 2
        assert var['name'] == 'VariableDeclaration'

        attributes = var['attributes']
        self._name = attributes['name']

        self._typeName = attributes['type']
        self._arrayDepth = 0
        self._isMapping = False
        self._mappingFrom = None
        self._mappingTo = False
        self._initial_expression = None
        self._type = None

        if 'constant' in attributes:
            self._is_constant = attributes['constant']

        self._analyze_variable_attributes(attributes)

        if not var['children']:
            # It happens on variable declared inside loop declaration
            try:
                self._type = ElementaryType(self._typeName)
                self._elem_to_parse = None
            except NonElementaryType:
                self._elem_to_parse = UnknownType(self._typeName)
        else:
            self._elem_to_parse = var['children'][0]

        if init: # there are two way to init a var local in the AST
            assert len(var['children']) <= 1
            self._initialized = True
            self._initializedNotParsed = init
        elif len(var['children']) == 1:
            self._initialized = False
            self._initializedNotParsed = []
        else:
            assert len(var['children']) == 2
            self._initialized = True
            self._initializedNotParsed = var['children'][1]

    def analyze(self, caller_context):
        # Can be re-analyzed due to inheritance
        if self._was_analyzed:
            return
        self._was_analyzed = True

        if self._elem_to_parse:
            self._type = parse_type(self._elem_to_parse, caller_context)
            self._elem_to_parse = None

        if self._initialized:
            self._initial_expression = parse_expression(self._initializedNotParsed, caller_context)
            self._initializedNotParsed = None
