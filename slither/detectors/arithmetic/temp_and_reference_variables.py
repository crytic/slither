from collections import defaultdict
from slither.slithir.variables import Constant, ReferenceVariable, TemporaryVariable

class Handle_TmpandRefer():

    def __init__(self):
        self._temp= defaultdict(list)
        self._constant = []
        self._index = []
        self._typeconv = []
        self._length = []


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
        self._index.append(ir.lvalue)


    #use list to store
    def handle_conversion(self, ir):
        var = ir.variable
        if isinstance(var, Constant):
            self._constant += [var]
            return
        
        if isinstance(var, (ReferenceVariable, TemporaryVariable)) and (var in self._temp):
            self._temp[ir.lvalue] = self._temp[var]
        else:
            self._temp[ir.lvalue] = [var]

        self._typeconv.append(ir.lvalue)


    def handle_length(self, ir):
        var = ir.value
        if isinstance(var, (ReferenceVariable, TemporaryVariable)) and (var in self._temp):
            self._temp[ir.lvalue] = self._temp[var]
        else:
            self._temp[ir.lvalue] = [var]
            
        self._length.append(ir.lvalue)

    
    @property
    def temp(self):
        return self._temp

    @property
    def constant(self):
        return self._constant
    
    @property
    def length(self):
        return self._length