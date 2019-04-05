from slither.core.variables.variable import Variable

class VariableDeclarationVyper(Variable):

    def __init__(self, var_record):
        '''
            A variable can be declared through a statement, or directly.
            If it is through a statement, the following children may contain
            the init value.
            It may be possible that the variable is declared through a statement,
            but the init value is declared at the VariableDeclaration children level
        '''
        super().__init__()
        self._var_record = var_record
        self._name = var_record.name
        self._type = var_record.typ
        self._initial_expression = None
        self._was_analyzed = False
        self._elem_to_parse = None
        self._initializedNotParsed = None

        self._reference_id = None

    def analyze(self):
        self._was_analyzed = True
        # TODO: check if need to handle _initial_expression
