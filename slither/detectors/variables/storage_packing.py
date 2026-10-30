from slither.core.declarations import Contract, Structure
from slither.core.solidity_types import ElementaryType, UserDefinedType
from slither.core.variables.variable import Variable
from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification
from slither.utils.output import Output


def suggested_order(variables: list[Variable]) -> tuple[list[Variable], int]:
    bins: list[list[Variable]] = []
    for variable in sorted(variables, key=lambda v: -v.type.storage_size[0]):
        size, _ = variable.type.storage_size
        for group in bins:
            if sum(v.type.storage_size[0] for v in group) + size <= 32:
                group.append(variable)
                break
        else:
            bins.append([variable])
    return [variable for group in bins for variable in group], len(bins)


class GasStoragePacking(AbstractDetector):
    ARGUMENT = "storage-packing"
    HELP = "Fixed-size storage fields that could occupy fewer slots"
    IMPACT = DetectorClassification.OPTIMIZATION
    CONFIDENCE = DetectorClassification.MEDIUM
    LANGUAGE = "solidity"
    WIKI = "https://github.com/crytic/slither/wiki/Detector-Documentation#storage-packing"
    WIKI_TITLE = "Storage packing"
    WIKI_DESCRIPTION = (
        "Finds a concrete order occupying fewer slots for all-elementary fixed-size state "
        "variables or struct fields. Skips state initializers, inheritance, recognised upgradeable contracts, custom "
        "storage layouts and contracts containing assembly. Constants, immutables and transient "
        "state are excluded. Fewer slots do not guarantee cheaper independent field writes."
    )
    WIKI_EXPLOIT_SCENARIO = """
```solidity
uint128 a; uint256 b; uint128 c; // three slots
// A fresh layout ordered as b, a, c occupies two slots.
```
"""
    WIKI_RECOMMENDATION = (
        "Consider the suggested order only for a fresh layout. Never reorder existing deployed "
        "storage, including structs in arrays or mappings. Review ABI and assembly dependencies "
        "and positional struct constructors, and benchmark field access patterns."
    )

    def _packing_result(
        self, owner: Contract | Structure, variables: list[Variable]
    ) -> list[Output]:
        if len(variables) < 2 or any(
            not isinstance(v.type, ElementaryType) or v.type.storage_size[1] for v in variables
        ):
            return []
        if isinstance(owner, Contract):
            if any(v.expression is not None for v in variables):
                return []
            before = len({self.compilation_unit.storage_layout_of(owner, v)[0] for v in variables})
        else:
            before = UserDefinedType(owner).storage_size[0] // 32
        order, after = suggested_order(variables)
        if after >= before:
            return []
        return [
            self.generate_result(
                [
                    owner,
                    f" could use {after} storage slots instead of {before} with field order ",
                    ", ".join(v.name for v in order),
                    ". Fresh layouts only: reordering deployed storage can corrupt data.\n",
                ],
                {
                    "slots_before": before,
                    "slots_after": after,
                    "suggested_order": [v.name for v in order],
                },
            )
        ]

    def _detect(self) -> list[Output]:
        results = []
        base_contracts = {base for contract in self.contracts for base in contract.inheritance}
        for contract in self.contracts:
            if (
                contract.inheritance
                or contract in base_contracts
                or len(self.compilation_unit.get_contract_from_name(contract.name)) != 1
                or contract.is_upgradeable
                or contract.is_upgradeable_proxy
                or contract.custom_storage_layout is not None
                or any(f.name in ("initialize", "reinitialize") for f in contract.functions)
                or any(f.contains_assembly for f in contract.functions_and_modifiers)
            ):
                continue
            results.extend(self._packing_result(contract, contract.storage_variables_ordered))
            for structure in contract.structures_declared:
                results.extend(self._packing_result(structure, structure.elems_ordered))
        return sorted(results, key=lambda r: r.data["description"])
