from slither.core.source_mapping.source_mapping import SourceMapping


class Expression(SourceMapping):
    def __init__(self):
        super().__init__()
        self._is_lvalue = False

    @property
    def is_lvalue(self) -> bool:
        return self._is_lvalue

    def set_lvalue(self) -> None:
        self._is_lvalue = True
