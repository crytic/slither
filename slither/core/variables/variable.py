"""
    Variable module
"""
from typing import Tuple, List

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

    ###################################################################################
    ###################################################################################
    # region Signature
    ###################################################################################
    ###################################################################################

    @property
    def signature(self) -> Tuple[str, List[str], List[str]]:
        """
            Return the signature of the state variable as a function signature
            :return: (str, list(str), list(str)), as (name, list parameters type, list return values type)
        """
        from slither.utils.type import export_nested_types_from_variable, export_return_type_from_variable
        return (self.name,
                [str(x) for x in export_nested_types_from_variable(self)],
                [str(x) for x in export_return_type_from_variable(self)])

    @property
    def signature_str(self):
        """
            Return the signature of the state variable as a function signature
            :return: str: func_name(type1,type2) returns(type3)
        """
        name, parameters, returnVars = self.signature
        return name + '(' + ','.join(parameters) + ') returns(' + ','.join(returnVars)  + ')'

    @property
    def solidity_signature(self):
        name, parameters, _ = self.signature
        return f'{name}({",".join(parameters)})'

    def __str__(self):
        return self._name


