from slither.core.source_mapping.source_mapping import SourceMapping
from slither.slithir.operations.lvalue import OperationWithLValue
from slither.slithir.utils.utils import is_valid_lvalue, is_valid_rvalue, RVALUE, LVALUE


class IndexRange(OperationWithLValue):
    """
    Array slice: lvalue = base[start:end]
    start and end are optional (None when omitted in the source).
    The result has the same type as the base (calldata array).
    """

    def __init__(
        self,
        result: LVALUE,
        base: RVALUE,
        start: RVALUE | None,
        end: RVALUE | None,
    ) -> None:
        super().__init__()
        assert is_valid_lvalue(result)
        assert is_valid_rvalue(base)
        assert start is None or is_valid_rvalue(start)
        assert end is None or is_valid_rvalue(end)
        self._base = base
        self._start = start
        self._end = end
        self._lvalue = result

    @property
    def read(self) -> list[SourceMapping]:
        return [v for v in [self._base, self._start, self._end] if v is not None]

    @property
    def base(self) -> RVALUE:
        return self._base

    @property
    def start(self) -> RVALUE | None:
        return self._start

    @property
    def end(self) -> RVALUE | None:
        return self._end

    def __str__(self) -> str:
        start = str(self.start) if self.start is not None else ""
        end = str(self.end) if self.end is not None else ""
        return f"{self.lvalue}({self.lvalue.type}) = {self.base}[{start}:{end}]"
