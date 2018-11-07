from slither.slithir.operations.high_level_call import HighLevelCall
from slither.core.declarations.contract import Contract

class LibraryCall(HighLevelCall):
    """
        High level message call
    """
    # Development function, to be removed once the code is stable
    def _check_destination(self, destination):
        assert isinstance(destination, (Contract))

    def __str__(self):
        gas = ''
        if self.call_gas:
            gas = 'gas:{}'.format(self.call_gas)
        arguments = []
        if self.arguments:
            arguments = self.arguments
        if not self.lvalue:
            lvalue = ''
        elif isinstance(self.lvalue.type, (list,)):
            lvalue = '{}({}) = '.format(self.lvalue, ','.join(str(x) for x in self.lvalue.type))
        else:
            lvalue = '{}({}) = '.format(self.lvalue, self.lvalue.type)
        txt = '{}LIBRARY_CALL, dest:{}, function:{}, arguments:{} {}'
        return txt.format(lvalue,
                          self.destination,
                          self.function_name,
                          [str(x) for x in arguments],
                          gas)



