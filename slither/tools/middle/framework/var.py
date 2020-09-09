from itertools import count
from typing import Union

from slither.core.variables.variable import Variable
from slither.slithir.variables import Constant


class SymVar:
    """
    Serves as an identifier for variables. Many SymVars can be used to represent
    the same SSA variable. This is because there may be many "instantiations" of
    the same variable in our graph.
    """
    counter = count()

    def __init__(self, var: Union[Variable, Constant]):
        self.var = var
        self.id = next(self.counter)

    def __str__(self):
        return 'sym_{}_{}'.format(self.var, self.id)

    def name(self):
        return 'sym_{}'.format(self.var)