from typing import List, Tuple, Any

from slither.core.solidity_types.type import Type
from slither.core.variables.function_type_variable import FunctionTypeVariable


class FunctionType(Type):
    def __init__(
        self,
        params: List[FunctionTypeVariable],
        return_values: List[FunctionTypeVariable],
    ) -> None:
        assert all(isinstance(x, FunctionTypeVariable) for x in params)
        assert all(isinstance(x, FunctionTypeVariable) for x in return_values)
        super().__init__()
        self._params: List[FunctionTypeVariable] = params
        self._return_values: List[FunctionTypeVariable] = return_values

    @property
    def params(self) -> List[FunctionTypeVariable]:
        return self._params

    @property
    def return_values(self) -> List[FunctionTypeVariable]:
        return self._return_values

    @property
    def return_type(self) -> List[Type]:
        return [x.type for x in self.return_values]

    @property
    def storage_size(self) -> Tuple[int, bool]:
        return 24, False

    @property
    def is_dynamic(self) -> bool:
        return False

    def __str__(self):
        # Use x.type
        # x.name may be empty
        params = ",".join([str(x.type) for x in self._params])
        return_values = ",".join([str(x.type) for x in self._return_values])
        if return_values:
            return f"function({params}) returns({return_values})"
        return f"function({params})"

    @property
    def parameters_signature(self) -> str:
        """
        Return the parameters signature(without the return statetement)
        """
        # Use x.type
        # x.name may be empty
        params = ",".join([str(x.type) for x in self._params])
        return f"({params})"

    @property
    def signature(self) -> str:
        """
        Return the signature(with the return statetement if it exists)
        """
        # Use x.type
        # x.name may be empty
        params = ",".join([str(x.type) for x in self._params])
        return_values = ",".join([str(x.type) for x in self._return_values])
        if return_values:
            return f"({params}) returns({return_values})"
        return f"({params})"

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, FunctionType):
            return False
        return self.params == other.params and self.return_values == other.return_values

    def __hash__(self):
        return hash(str(self))
