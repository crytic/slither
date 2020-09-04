from collections import defaultdict

from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification


def _find_missing_inheritance(slither):
    """
    Filter contracts with missing inheritance to return only the "most base" contracts
    in the inheritance tree.
    :param slither:
    :return:
    """
    missings = slither.contracts_with_missing_inheritance

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
    WIKI_DESCRIPTION = """If a codebase has two contracts the similar names, the compilation artifacts
will not contain one of the contracts with the duplicate name."""
    WIKI_EXPLOIT_SCENARIO = """
Bob's `truffle` codebase has two contracts named `ERC20`.
When `truffle compile` runs, only one of the two contracts will generate artifacts in `build/contracts`.
As a result, the second contract cannot be analyzed.
"""
    WIKI_RECOMMENDATION = "Rename the contract."

    def _detect(self):  # pylint: disable=too-many-locals,too-many-branches
        results = []

        names_reused = self.slither.contract_name_collisions

        # First show the contracts that we know are missing
        incorrectly_constructed = [
            contract for contract in self.contracts if contract.is_incorrectly_constructed
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
        most_base_with_missing_inheritance = _find_missing_inheritance(self.slither)

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
