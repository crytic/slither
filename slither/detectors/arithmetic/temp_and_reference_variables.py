from collections import defaultdict
from typing import List
from slither.slithir.operations import Index, TypeConversion
from slither.slithir.variables import Constant, ReferenceVariable, TemporaryVariable

class Handle_TmpandRefer():

    def __init__(self):
        self._temp= defaultdict(list)
        self._constant = []

    #use tuple to store ()
    def handle_index(self, ir):
        (var, index) = ir.read

        if isinstance(var, (ReferenceVariable, TemporaryVariable)) and (var in self._temp):
            var = self._temp[var]
            if len(var) == 1:
                var = var[0]

        if (not isinstance(index, Constant) and 
            isinstance(index, (ReferenceVariable, TemporaryVariable)) and 
            index in self._temp
        ):
            index = self._temp[index]
            if len(index) == 1:
                index = index[0]
        
        self._temp[ir.lvalue] = (var, index)

    #use list to store
    def handle_conversion(self, ir):
        
        if isinstance(ir.variable, Constant):
            self._constant += [ir.lvalue]
            return
            
        var = ir.variable
        if isinstance(var, (ReferenceVariable, TemporaryVariable)) and (var in self._temp):
            self._temp[ir.lvalue] = var
        else:
            self._temp[ir.lvalue] = [var]
    
    @property
    def temp(self):
        return self._temp

    @property
    def constant(self):
        return self._constant