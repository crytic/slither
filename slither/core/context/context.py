class Context:

    def __init__(self):
        super(Context, self).__init__()
        self._context = {}

    @property
    def context(self):
        '''
        Dict used by analysis
        '''
        return self._context


