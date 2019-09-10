from pathlib import Path
import re
import logging
from slither.exceptions import SlitherException

logger = logging.getLogger("Slither-flattening")

class Flattening:

    DEFAULT_EXPORT_PATH = Path('crytic-export/flattening')

    def __init__(self, slither, external_to_public=False):
        self._source_codes = {}
        self._slither = slither
        self._external_to_public = external_to_public

        for contract in slither.contracts:
            self._get_source_code(contract)

    def _get_source_code(self, contract):
        src_mapping = contract.source_mapping
        content = self._slither.source_code[src_mapping['filename_absolute']]
        start = src_mapping['start']
        end = src_mapping['start'] + src_mapping['length']

        if self._external_to_public:
            to_patch = []
            for f in contract.functions_declared:
                if f.visibility == 'external':
                    attributes_start = int(f.parameters_src.source_mapping['start'] +
                                           f.parameters_src.source_mapping['length'])
                    attributes_end = int(f.returns_src.source_mapping['start'])
                    attributes = content[attributes_start:attributes_end]
                    regex = re.search(r'((\sexternal)\s+)|(\sexternal)$|(\)external)$', attributes)
                    if regex:
                        to_patch.append(attributes_start + regex.span()[0] + 1)
                    else:
                        raise SlitherException(f'External keyword not found {f.name} {attributes}')
            to_patch.sort(reverse=True)

            print(to_patch)
            content = content[start:end]
            for index in to_patch:
                index = index - start
                content = content[:index] + 'public' + content[index + len('external'):]
        else:
            content = content[start:end]

        self._source_codes[contract] = content


    def _export_contract(self, contract, exported, list_contract):
        if contract.name in exported:
            return
        for inherited in contract.inheritance:
            self._export_contract(inherited, exported, list_contract)

        externals = contract.all_library_calls + contract.all_high_level_calls
        # externals is a list of (contract, function)
        # We also filter call to itself to avoid infilite loop
        externals = list(set([e[0] for e in externals if e[0] != contract]))

        for inherited in externals:
            self._export_contract(inherited, exported, list_contract)

        exported.add(contract.name)
        list_contract.append(self._source_codes[contract])


    def export(self, target=None):

        if not self.DEFAULT_EXPORT_PATH.exists():
            self.DEFAULT_EXPORT_PATH.mkdir(parents=True)

        if target is None:
            for contract in self._slither.contracts_derived:
                ret = []
                self._export_contract(contract, set(), ret)
                path = Path(self.DEFAULT_EXPORT_PATH, f'{contract.name}.sol')
                logger.info(f'Export {path}')
                with open(path, 'w') as f:
                    f.write('\n'.join(ret))
                    f.write('\n')
