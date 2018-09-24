class Operation(object):

    @property
    def read(self):
        """
            Must be ovveriden
        """
        raise Exception('Not overrided {}'.format(type(self)))
