from collections import defaultdict

from slither.core.compilation_unit import SlitherCompilationUnit
from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification


def _find_missing_inheritance(compilation_unit: SlitherCompilationUnit):
    """
    Filter contracts with missing inheritance to return only the "most base" contracts
    in the inheritance tree.
    :param slither:
    :return:
    """
    missings = compilation_unit.contracts_with_missing_inheritance

    ret = []
    for b in missings:
        is_most_base = True
        for inheritance in b.immediate_inheritance:
            if inheritance in missings:
                is_most_base = False
        if is_most_base:
            ret.append(b)

    return ret


class NameReused(AbstractDetector):
    ARGUMENT = "name-reused"
    HELP = "Contract's name reused"
    IMPACT = DetectorClassification.HIGH
    CONFIDENCE = DetectorClassification.HIGH

    WIKI = "https://github.com/crytic/slither/wiki/Detector-Documentation#name-reused"

    WIKI_TITLE = "Name reused"

    # region wiki_description
    WIKI_DESCRIPTION = """If a codebase has two contracts the similar names, the compilation artifacts
will not contain one of the contracts with the duplicate name."""
    # endregion wiki_description

    # region wiki_exploit_scenario
    WIKI_EXPLOIT_SCENARIO = """
Bob's `truffle` codebase has two contracts named `ERC20`.
When `truffle compile` runs, only one of the two contracts will generate artifacts in `build/contracts`.
As a result, the second contract cannot be analyzed.
"""
    # endregion wiki_exploit_scenario

    WIKI_RECOMMENDATION = "Rename the contract."

    def _detect(self):  # pylint: disable=too-many-locals,too-many-branches
        results = []
        compilation_unit = self.compilation_unit

        all_contracts = compilation_unit.contracts
        all_contracts_name = [c.name for c in all_contracts]
        contracts_name_reused = {
            contract for contract in all_contracts_name if all_contracts_name.count(contract) > 1
        }

        names_reused = {
            name: compilation_unit.get_contract_from_name(name) for name in contracts_name_reused
        }

        # First show the contracts that we know are missing
        incorrectly_constructed = [
            contract
            for contract in compilation_unit.contracts
            if contract.is_incorrectly_constructed
        ]

        inheritance_corrupted = defaultdict(list)
        for contract in incorrectly_constructed:
            for father in contract.inheritance:
                inheritance_corrupted[father.name].append(contract)

        for contract_name, files in names_reused.items():
            info = [contract_name, " is re-used:\n"]
            for file in files:
                if file is None:
                    info += ["\t- In an file not found, most likely in\n"]
                else:
                    info += ["\t- ", file, "\n"]

            if contract_name in inheritance_corrupted:
                info += ["\tAs a result, the inherited contracts are not correctly analyzed:\n"]
            for corrupted in inheritance_corrupted[contract_name]:
                info += ["\t\t- ", corrupted, "\n"]
            res = self.generate_result(info)
            results.append(res)

        # Then show the contracts for which one of the father was not found
        # Here we are not able to know
        most_base_with_missing_inheritance = _find_missing_inheritance(compilation_unit)

        for b in most_base_with_missing_inheritance:
            info = [b, " inherits from a contract for which the name is reused.\n"]
            if b.inheritance:
                info += ["\t- Slither could not determine which contract has a duplicate name:\n"]
                for inheritance in b.inheritance:
                    info += ["\t\t-", inheritance, "\n"]
                info += ["\t- Check if:\n"]
                info += ["\t\t- A inherited contract is missing from this list,\n"]
                info += ["\t\t- The contract are imported from the correct files.\n"]
            if b.derived_contracts:
                info += [f"\t- This issue impacts the contracts inheriting from {b.name}:\n"]
                for derived in b.derived_contracts:
                    info += ["\t\t-", derived, "\n"]
            res = self.generate_result(info)
            results.append(res)
        return results
