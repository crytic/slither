"""
    Variable module
"""

from slither.core.source_mapping.source_mapping import SourceMapping
from slither.core.solidity_types.type import Type
from slither.core.solidity_types.elementary_type import ElementaryType

class Variable(SourceMapping):

    def __init__(self):
        super(Variable, self).__init__()
        self._name = None
        self._initial_expression = None
        self._type = None
        self._initialized = None
        self._visibility = None
        self._is_constant = False

    @property
    def expression(self):
        """
            Expression: Expression of the node (if initialized)
            Initial expression may be different than the expression of the node
            where the variable is declared, if its used ternary operator
            Ex: uint a = b?1:2
            The expression associated to a is uint a = b?1:2
            But two nodes are created,
            one where uint a = 1,
            and one where uint a = 2

        """
        return self._initial_expression

    @property
    def initialized(self):
        """
            boolean: True if the variable is initialized at construction
        """
        return self._initialized

    @property
    def uninitialized(self):
        """
            boolean: True if the variable is not initialized
        """
        return not self._initialized

    @property
    def name(self):
        '''
            str: variable name
        '''
        return self._name

    @name.setter
    def name(self, name):
        self._name = name

    @property
    def type(self):
        return self._type

    @property
    def is_constant(self):
        return self._is_constant

    @property
    def visibility(self):
        '''
            str: variable visibility
        '''
        return self._visibility

    def set_type(self, t):
        if isinstance(t, str):
            t = ElementaryType(t)
        assert isinstance(t, (Type, list)) or t is None
        self._type = t


    def __str__(self):
        return self._name


