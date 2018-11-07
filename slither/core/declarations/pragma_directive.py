from slither.core.source_mapping.source_mapping import SourceMapping

class Pragma(SourceMapping):

    def __init__(self, directive):
        super(Pragma, self).__init__()
        self._directive = directive

    @property
    def directive(self):
        '''
            list(str)
        '''
        return self._directive

    @property
    def version(self):
        return ''.join(self.directive[1:])

    def __str__(self):
        return 'pragma '+''.join(self.directive)
