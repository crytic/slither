from slither.slithir.operations.high_level_call import HighLevelCall
from slither.core.declarations.contract import Contract


# TODO: use the usefor declaration

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
        return str(self.lvalue) +' = LIBRARY_CALL dest:{} function:{} arguments:{} {}'.format(self.destination, self.function_name, [str(x) for x in arguments], gas)
#        if self.call_id:
#            call_id = '(id ({}))'.format(self.call_id)
#        return str(self.lvalue) +' = EXTERNALCALL dest:{} function:{} (#arg {}) {}'.format(self.destination, self.function_name, self.nbr_arguments)


