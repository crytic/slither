from collections import defaultdict

from slither.detectors.abstract_detector import (AbstractDetector,
                                                 DetectorClassification)


def _find_missing_inheritance(slither):
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
    ARGUMENT = 'name-reused'
    HELP = "Contract's name reused"
    IMPACT = DetectorClassification.HIGH
    CONFIDENCE = DetectorClassification.HIGH

    WIKI = 'https://github.com/crytic/slither/wiki/Detector-Documentation#name-reused'

    WIKI_TITLE = 'Name reused'
    WIKI_DESCRIPTION = 'todo'
    WIKI_EXPLOIT_SCENARIO = 'todo'
    WIKI_RECOMMENDATION = 'Rename the contract.'

    def _detect(self):
        results = []

        names_reused = self.slither.contract_name_collisions

        incorrectly_constructed = [contract for contract in self.contracts
                                   if contract.is_incorrectly_constructed]

        inheritance_corrupted = defaultdict(list)
        for contract in incorrectly_constructed:
            for father in contract.inheritance:
                inheritance_corrupted[father.name].append(contract)

        for contract_name, files in names_reused.items():
            info = [contract_name, ' is re-used:\n']
            for file in files:
                if file is None:
                    info += ['\t- In an file not found, most likely in\n']
                else:
                    info += ['\t- ', file, '\n']

            if contract_name in inheritance_corrupted:
                info += ['\tAs a result, the inherited contracts are not correctly analyzed:\n']
            for corrupted in inheritance_corrupted[contract_name]:
                info += ["\t\t- ", corrupted, '\n']
            res = self.generate_result(info)
            results.append(res)

        most_base_with_missing_inheritance = _find_missing_inheritance(self.slither)

        for b in most_base_with_missing_inheritance:
            info = [b, ' inherits from a contract for which the name is reused.\n',
                    'Slither could not determine the contract, but it is either:\n']
            for inheritance in b.immediate_inheritance:
                info += ['\t-', inheritance, '\n']
            info += [b, ' and all the contracts inheriting from it are not correctly analyzed:\n']
            for derived in b.derived_contracts:
                info += ['\t-', derived, '\n']
            res = self.generate_result(info)
            results.append(res)
        return results
