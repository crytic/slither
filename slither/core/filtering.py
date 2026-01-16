import enum
import re
from dataclasses import dataclass
from typing import TYPE_CHECKING, Union


if TYPE_CHECKING:
    from slither.core.declarations import Contract, FunctionContract


class FilteringAction(enum.Enum):
    ALLOW = enum.auto()
    REJECT = enum.auto()


@dataclass
class FilteringRule:
    type: FilteringAction = FilteringAction.ALLOW
    path: Union[re.Pattern, None] = None
    contract: Union[re.Pattern, None] = None
    function: Union[re.Pattern, None] = None

    def match_contract(self, contract: "Contract") -> bool:
        """Check with this filter matches the contract.

        Verity table is as followed:
                            path
            |        | None     | True  | False |
        co  |-----------------------------------|
        nt  | None  || default  | True  | False |
        ra  | True  || True     | True  | False |
        ct  | False || False    | False | False |

        """

        # If we have no constraint, we just follow the default rule
        if self.path is None and self.contract is None:
            return self.type == FilteringAction.ALLOW

        path_match = None
        if self.path is not None:
            path_match = bool(re.search(self.path, contract.source_mapping.filename.short))

        contract_match = None
        if self.contract is not None:
            contract_match = bool(re.search(self.contract, contract.name))

        if path_match is None:
            return contract_match

        if contract_match is None:
            return path_match

        if contract_match and path_match:
            return True

        return False

    def match_function(self, function: "FunctionContract") -> bool:
        """Check if this filter apply to this element."""
        # If we have no constraint, follow default rule
        if self.function is None:
            return self.type == FilteringAction.ALLOW

        return bool(re.search(self.function, function.name))
