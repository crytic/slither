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

    @property
    def name(self):
        return self.version

    @property
    def is_solidity_version(self):
        if len(self._directive) > 0:
            return self._directive[0].lower() == 'solidity'
        return False

    @property
    def is_abi_encoder_v2(self):
        if len(self._directive) == 2:
            return self._directive[0] == 'experimental' and self._directive[1] == 'ABIEncoderV2'
        return False

    def __str__(self):
        return 'pragma '+''.join(self.directive)
