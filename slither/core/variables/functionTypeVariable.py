"""
    Variable used with FunctionType
    ex:
    struct C{
        function(uint) my_func;
    }
"""

from .variable import Variable

class FunctionTypeVariable(Variable): pass

