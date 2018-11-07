
from .variable_declaration import VariableDeclarationSolc
from slither.core.variables.local_variable import LocalVariable

class LocalVariableSolc(VariableDeclarationSolc, LocalVariable):

    def _analyze_variable_attributes(self, attributes):
        ''''
            Variable Location
            Can be storage/memory or default
        '''
        if 'storageLocation' in attributes:
            location = attributes['storageLocation']
            self._location = location
        else:
            if 'memory' in attributes['type']:
                self._location = 'memory'
            elif'storage' in attributes['type']:
                self._location = 'storage'
            else:
                self._location = 'default'

        super(LocalVariableSolc, self)._analyze_variable_attributes(attributes)

