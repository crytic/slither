from pathlib import Path
import re
import logging
from slither.exceptions import SlitherException
from slither.core.solidity_types.user_defined_type import UserDefinedType
from slither.core.declarations.structure import Structure
from slither.core.declarations.enum import Enum
from slither.core.declarations.contract import Contract
from slither.slithir.operations import NewContract, TypeConversion

logger = logging.getLogger("Slither-flattening")

class Flattening:

    DEFAULT_EXPORT_PATH = Path('crytic-export/flattening')

    def __init__(self, slither, external_to_public=False):
        self._source_codes = {}
        self._slither = slither
        self._external_to_public = external_to_public
        self._use_abi_encoder_v2 = False

        self._check_abi_encoder_v2()

        for contract in slither.contracts:
            self._get_source_code(contract)

    def _check_abi_encoder_v2(self):
        for p in self._slither.pragma_directives:
            if 'ABIEncoderV2' in str(p.directive):
                self._use_abi_encoder_v2 = True
                return

    def _get_source_code(self, contract):
        src_mapping = contract.source_mapping
        content = self._slither.source_code[src_mapping['filename_absolute']]
        start = src_mapping['start']
        end = src_mapping['start'] + src_mapping['length']

        # interface must use external
        if self._external_to_public and contract.contract_kind != "interface":
            # to_patch is a list of (index, bool). The bool indicates
            # if the index is for external -> public (true)
            # or a calldata -> memory (false)
            to_patch = []
            for f in contract.functions_declared:
                # fallback must be external
                if f.is_fallback or f.is_constructor_variables:
                    continue
                if f.visibility == 'external':
                    attributes_start = (f.parameters_src.source_mapping['start'] +
                                        f.parameters_src.source_mapping['length'])
                    attributes_end = f.returns_src.source_mapping['start']
                    attributes = content[attributes_start:attributes_end]
                    regex = re.search(r'((\sexternal)\s+)|(\sexternal)$|(\)external)$', attributes)
                    if regex:
                        to_patch.append((attributes_start + regex.span()[0] + 1, True))
                    else:
                        raise SlitherException(f'External keyword not found {f.name} {attributes}')

                    for var in f.parameters:
                        if var.location == "calldata":
                            calldata_start = var.source_mapping['start']
                            calldata_end = calldata_start + var.source_mapping['length']
                            calldata_idx = content[calldata_start:calldata_end].find(' calldata ')
                            to_patch.append((calldata_start + calldata_idx + 1, False))

            to_patch.sort(key=lambda x:x[0], reverse=True)

            content = content[start:end]
            for (index, is_external) in to_patch:
                index = index - start
                if is_external:
                    content = content[:index] + 'public' + content[index + len('external'):]
                else:
                    content = content[:index] + 'memory' + content[index + len('calldata'):]
        else:
            content = content[start:end]

        self._source_codes[contract] = content


    def _export_from_type(self, t, contract, exported, list_contract):
        if isinstance(t, UserDefinedType):
            if isinstance(t.type, (Enum, Structure)):
                if t.type.contract != contract and not t.type.contract in exported:
                    self._export_contract(t.type.contract, exported, list_contract)
            else:
                assert isinstance(t.type, Contract)
                if t.type != contract and not t.type in exported:
                    self._export_contract(t.type, exported, list_contract)

    def _export_contract(self, contract, exported, list_contract):
        if contract.name in exported:
            return
        for inherited in contract.inheritance:
            self._export_contract(inherited, exported, list_contract)

        # Find all the external contracts called
        externals = contract.all_library_calls + contract.all_high_level_calls
        # externals is a list of (contract, function)
        # We also filter call to itself to avoid infilite loop
        externals = list(set([e[0] for e in externals if e[0] != contract]))

        for inherited in externals:
            self._export_contract(inherited, exported, list_contract)

        # Find all the external contracts use as a base type
        local_vars = []
        for f in contract.functions_declared:
            local_vars += f.variables

        for v in contract.variables + local_vars:
            self._export_from_type(v.type, contract, exported, list_contract)

        # Find all convert and "new" operation that can lead to use an external contract
        for f in contract.functions_declared:
            for ir in f.slithir_operations:
                if isinstance(ir, NewContract):
                    if ir.contract_created != contract and not ir.contract_created in exported:
                        self._export_contract(ir.contract_created, exported, list_contract)
                if isinstance(ir, TypeConversion):
                    self._export_from_type(ir.type, contract, exported, list_contract)
        if contract.name in exported:
            return
        exported.add(contract.name)
        list_contract.append(self._source_codes[contract])

    def _export(self, contract, ret):
        self._export_contract(contract, set(), ret)
        path = Path(self.DEFAULT_EXPORT_PATH, f'{contract.name}.sol')
        logger.info(f'Export {path}')
        with open(path, 'w') as f:
            if self._slither.solc_version:
                f.write(f'pragma solidity {self._slither.solc_version};\n')
            if self._use_abi_encoder_v2:
                f.write('pragma experimental ABIEncoderV2;\n')
            f.write('\n'.join(ret))
            f.write('\n')

    def export(self, target=None):

        if not self.DEFAULT_EXPORT_PATH.exists():
            self.DEFAULT_EXPORT_PATH.mkdir(parents=True)

        if target is None:
            for contract in self._slither.contracts_derived:
                ret = []
                self._export(contract, ret)
        else:
            contract = self._slither.get_contract_from_name(target)
            if contract is None:
                logger.error(f'{target} not found')
            else:
                ret = []
                self._export(contract, ret)

