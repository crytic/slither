import logging
from slither.solc_parsing.expressions.expression_parsing import parse_expression

from slither.core.variables.variable import Variable

from slither.vyper_parsing.vyper_types.type_parsing import parse_type


logger = logging.getLogger("VariableDeclarationSolcParsing")


class VariableDeclarationVyper(Variable):

    def __init__(self, var):
        '''
            A variable can be declared through a statement, or directly.
            If it is through a statement, the following children may contain
            the init value.
            It may be possible that the variable is declared through a statement,
            but the init value is declared at the VariableDeclaration children level
        '''

        super(VariableDeclarationVyper, self).__init__()

        # TODO: this will only work for argument, not all variables
        self._name = var['arg']
        if 'id' in var['annotation']:
            self._type = parse_type(var['annotation']['id'])
        elif 'func' in var['annotation']:
            self._type = parse_type(var['annotation']['func']['id'])





