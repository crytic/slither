from slither.core.context.context import Context
class Operation(Context):

    @property
    def read(self):
        """
            Must be ovveriden
        """
        raise Exception('Not overrided {}'.format(type(self)))
