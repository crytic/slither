import logging
import re
import uuid
from collections import namedtuple
from enum import Enum as PythonEnum
from pathlib import Path
from typing import List, Set, Dict, Optional

from slither.core.compilation_unit import SlitherCompilationUnit
from slither.core.declarations import SolidityFunction, EnumContract, StructureContract
from slither.core.declarations.contract import Contract
from slither.core.declarations.function_top_level import FunctionTopLevel
from slither.core.declarations.top_level import TopLevel
from slither.core.solidity_types import MappingType, ArrayType
from slither.core.solidity_types.type import Type
from slither.core.solidity_types.user_defined_type import UserDefinedType
from slither.exceptions import SlitherException
from slither.slithir.operations import NewContract, TypeConversion, SolidityCall, InternalCall
from slither.tools.flattening.export.export import (
    Export,
    export_as_json,
    save_to_zip,
    save_to_disk,
)

logger = logging.getLogger("Slither-flattening")

# index: where to start
# patch_type:
#   - public_to_external: public to external (external-to-public)
#   - calldata_to_memory: calldata to memory (external-to-public)
#   - line_removal: remove the line (remove-assert)
Patch = namedtuple("PatchExternal", ["index", "patch_type"])


class Strategy(PythonEnum):
    MostDerived = 0
    OneFile = 1
    LocalImport = 2


STRATEGIES_NAMES = ",".join([i.name for i in Strategy])

DEFAULT_EXPORT_PATH = Path("crytic-export/flattening")


class Flattening:
    # pylint: disable=too-many-instance-attributes,too-many-arguments,too-many-locals,too-few-public-methods
    def __init__(
        self,
        compilation_unit: SlitherCompilationUnit,
        external_to_public=False,
        remove_assert=False,
        private_to_internal=False,
        export_path: Optional[str] = None,
        pragma_solidity: Optional[str] = None,
    ):
        self._source_codes: Dict[Contract, str] = {}
        self._source_codes_top_level: Dict[TopLevel, str] = {}
        self._compilation_unit: SlitherCompilationUnit = compilation_unit
        self._external_to_public = external_to_public
        self._remove_assert = remove_assert
        self._use_abi_encoder_v2 = False
        self._private_to_internal = private_to_internal
        self._pragma_solidity = pragma_solidity

        self._export_path: Path = DEFAULT_EXPORT_PATH if export_path is None else Path(export_path)

        self._check_abi_encoder_v2()

        for contract in compilation_unit.contracts:
            self._get_source_code(contract)

        self._get_source_code_top_level(compilation_unit.structures_top_level)
        self._get_source_code_top_level(compilation_unit.enums_top_level)
        self._get_source_code_top_level(compilation_unit.variables_top_level)
        self._get_source_code_top_level(compilation_unit.functions_top_level)

    def _get_source_code_top_level(self, elems: List[TopLevel]) -> None:
        for elem in elems:
            src_mapping = elem.source_mapping
            content = self._compilation_unit.core.source_code[src_mapping["filename_absolute"]]
            start = src_mapping["start"]
            end = src_mapping["start"] + src_mapping["length"]
            self._source_codes_top_level[elem] = content[start:end]

    def _check_abi_encoder_v2(self):
        """
        Check if ABIEncoderV2 is required
        Set _use_abi_encorder_v2
        :return:
        """
        for p in self._compilation_unit.pragma_directives:
            if "ABIEncoderV2" in str(p.directive):
                self._use_abi_encoder_v2 = True
                return

    def _get_source_code(
        self, contract: Contract
    ):  # pylint: disable=too-many-branches,too-many-statements
        """
        Save the source code of the contract in self._source_codes
        Patch the source code
        :param contract:
        :return:
        """
        src_mapping = contract.source_mapping
        content = self._compilation_unit.core.source_code[src_mapping["filename_absolute"]]
        start = src_mapping["start"]
        end = src_mapping["start"] + src_mapping["length"]

        to_patch = []
        # interface must use external
        if self._external_to_public and not contract.is_interface:
            for f in contract.functions_declared:
                # fallback must be external
                if f.is_fallback or f.is_constructor_variables:
                    continue
                if f.visibility == "external":
                    attributes_start = (
                        f.parameters_src().source_mapping["start"]
                        + f.parameters_src().source_mapping["length"]
                    )
                    attributes_end = f.returns_src().source_mapping["start"]
                    attributes = content[attributes_start:attributes_end]
                    regex = re.search(r"((\sexternal)\s+)|(\sexternal)$|(\)external)$", attributes)
                    if regex:
                        to_patch.append(
                            Patch(
                                attributes_start + regex.span()[0] + 1,
                                "public_to_external",
                            )
                        )
                    else:
                        raise SlitherException(f"External keyword not found {f.name} {attributes}")

                    for var in f.parameters:
                        if var.location == "calldata":
                            calldata_start = var.source_mapping["start"]
                            calldata_end = calldata_start + var.source_mapping["length"]
                            calldata_idx = content[calldata_start:calldata_end].find(" calldata ")
                            to_patch.append(
                                Patch(
                                    calldata_start + calldata_idx + 1,
                                    "calldata_to_memory",
                                )
                            )

        if self._private_to_internal:
            for variable in contract.state_variables_declared:
                if variable.visibility == "private":
                    attributes_start = variable.source_mapping["start"]
                    attributes_end = attributes_start + variable.source_mapping["length"]
                    attributes = content[attributes_start:attributes_end]
                    regex = re.search(r" private ", attributes)
                    if regex:
                        to_patch.append(
                            Patch(
                                attributes_start + regex.span()[0] + 1,
                                "private_to_internal",
                            )
                        )
                    else:
                        raise SlitherException(
                            f"private keyword not found {variable.name} {attributes}"
                        )

        if self._remove_assert:
            for function in contract.functions_and_modifiers_declared:
                for node in function.nodes:
                    for ir in node.irs:
                        if isinstance(ir, SolidityCall) and ir.function == SolidityFunction(
                            "assert(bool)"
                        ):
                            to_patch.append(Patch(node.source_mapping["start"], "line_removal"))
                            logger.info(
                                f"Code commented: {node.expression} ({node.source_mapping_str})"
                            )

        to_patch.sort(key=lambda x: x.index, reverse=True)

        content = content[start:end]
        for patch in to_patch:
            patch_type = patch.patch_type
            index = patch.index
            index = index - start
            if patch_type == "public_to_external":
                content = content[:index] + "public" + content[index + len("external") :]
            elif patch_type == "private_to_internal":
                content = content[:index] + "internal" + content[index + len("private") :]
            elif patch_type == "calldata_to_memory":
                content = content[:index] + "memory" + content[index + len("calldata") :]
            else:
                assert patch_type == "line_removal"
                content = content[:index] + " // " + content[index:]

        self._source_codes[contract] = content

    def _pragmas(self) -> str:
        """
        Return the required pragmas
        :return:
        """
        ret = ""
        if self._pragma_solidity:
            ret += f"pragma solidity {self._pragma_solidity};\n"
        else:
            # TODO support multiple compiler version
            ret += f"pragma solidity {list(self._compilation_unit.crytic_compile.compilation_units.values())[0].compiler_version.version};\n"

        if self._use_abi_encoder_v2:
            ret += "pragma experimental ABIEncoderV2;\n"
        return ret

    def _export_from_type(
        self,
        t: Type,
        contract: Contract,
        exported: Set[str],
        list_contract: List[Contract],
        list_top_level: List[TopLevel],
    ):
        if isinstance(t, UserDefinedType):
            t_type = t.type
            if isinstance(t_type, (EnumContract, StructureContract)):
                if t_type.contract != contract and t_type.contract not in exported:
                    self._export_list_used_contracts(
                        t_type.contract, exported, list_contract, list_top_level
                    )
            else:
                assert isinstance(t.type, Contract)
                if t.type != contract and t.type not in exported:
                    self._export_list_used_contracts(
                        t.type, exported, list_contract, list_top_level
                    )
        elif isinstance(t, MappingType):
            self._export_from_type(t.type_from, contract, exported, list_contract, list_top_level)
            self._export_from_type(t.type_to, contract, exported, list_contract, list_top_level)
        elif isinstance(t, ArrayType):
            self._export_from_type(t.type, contract, exported, list_contract, list_top_level)

    def _export_list_used_contracts(  # pylint: disable=too-many-branches
        self,
        contract: Contract,
        exported: Set[str],
        list_contract: List[Contract],
        list_top_level: List[TopLevel],
    ):
        # TODO: investigate why this happen
        if not isinstance(contract, Contract):
            return
        if contract.name in exported:
            return
        exported.add(contract.name)
        for inherited in contract.inheritance:
            self._export_list_used_contracts(inherited, exported, list_contract, list_top_level)

        # Find all the external contracts called
        externals = contract.all_library_calls + contract.all_high_level_calls
        # externals is a list of (contract, function)
        # We also filter call to itself to avoid infilite loop
        externals = list({e[0] for e in externals if e[0] != contract})

        for inherited in externals:
            self._export_list_used_contracts(inherited, exported, list_contract, list_top_level)

        for list_libs in contract.using_for.values():
            for lib_candidate_type in list_libs:
                if isinstance(lib_candidate_type, UserDefinedType):
                    lib_candidate = lib_candidate_type.type
                    if isinstance(lib_candidate, Contract):
                        self._export_list_used_contracts(
                            lib_candidate, exported, list_contract, list_top_level
                        )

        # Find all the external contracts use as a base type
        local_vars = []
        for f in contract.functions_declared:
            local_vars += f.variables

        for v in contract.variables + local_vars:
            self._export_from_type(v.type, contract, exported, list_contract, list_top_level)

        for s in contract.structures:
            for elem in s.elems.values():
                self._export_from_type(elem.type, contract, exported, list_contract, list_top_level)

        # Find all convert and "new" operation that can lead to use an external contract
        for f in contract.functions_declared:
            for ir in f.slithir_operations:
                if isinstance(ir, NewContract):
                    if ir.contract_created != contract and not ir.contract_created in exported:
                        self._export_list_used_contracts(
                            ir.contract_created, exported, list_contract, list_top_level
                        )
                if isinstance(ir, TypeConversion):
                    self._export_from_type(
                        ir.type, contract, exported, list_contract, list_top_level
                    )

                for read in ir.read:
                    if isinstance(read, TopLevel):
                        if read not in list_top_level:
                            list_top_level.append(read)
                if isinstance(ir, InternalCall):
                    function_called = ir.function
                    if isinstance(function_called, FunctionTopLevel):
                        list_top_level.append(function_called)

        if contract not in list_contract:
            list_contract.append(contract)

    def _export_contract_with_inheritance(self, contract) -> Export:
        list_contracts: List[Contract] = []  # will contain contract itself
        list_top_level: List[TopLevel] = []
        self._export_list_used_contracts(contract, set(), list_contracts, list_top_level)
        path = Path(self._export_path, f"{contract.name}_{uuid.uuid4()}.sol")

        content = ""
        content += self._pragmas()

        for listed_top_level in list_top_level:
            content += self._source_codes_top_level[listed_top_level]
            content += "\n"

        for listed_contract in list_contracts:
            content += self._source_codes[listed_contract]
            content += "\n"

        return Export(filename=path, content=content)

    def _export_most_derived(self) -> List[Export]:
        ret: List[Export] = []
        for contract in self._compilation_unit.contracts_derived:
            ret.append(self._export_contract_with_inheritance(contract))
        return ret

    def _export_all(self) -> List[Export]:
        path = Path(self._export_path, "export.sol")

        content = ""
        content += self._pragmas()

        for top_level_content in self._source_codes_top_level.values():
            content += "\n"
            content += top_level_content
            content += "\n"

        contract_seen = set()
        contract_to_explore = list(self._compilation_unit.contracts)

        # We only need the inheritance order here, as solc can compile
        # a contract that use another contract type (ex: state variable) that he has not seen yet
        while contract_to_explore:
            next_to_explore = contract_to_explore.pop(0)

            if not next_to_explore.inheritance or all(
                (father in contract_seen for father in next_to_explore.inheritance)
            ):
                content += "\n"
                content += self._source_codes[next_to_explore]
                content += "\n"
                contract_seen.add(next_to_explore)
            else:
                contract_to_explore.append(next_to_explore)

        return [Export(filename=path, content=content)]

    def _export_with_import(self) -> List[Export]:
        exports: List[Export] = []
        for contract in self._compilation_unit.contracts:
            list_contracts: List[Contract] = []  # will contain contract itself
            list_top_level: List[TopLevel] = []
            self._export_list_used_contracts(contract, set(), list_contracts, list_top_level)

            if list_top_level:
                logger.info(
                    "Top level objects are not yet supported with the local import flattening"
                )
                for elem in list_top_level:
                    logger.info(f"Missing {elem} for {contract.name}")

            path = Path(self._export_path, f"{contract.name}.sol")

            content = ""
            content += self._pragmas()
            for used_contract in list_contracts:
                if used_contract != contract:
                    content += f"import './{used_contract.name}.sol';\n"
            content += "\n"
            content += self._source_codes[contract]
            content += "\n"
            exports.append(Export(filename=path, content=content))
        return exports

    def export(  # pylint: disable=too-many-arguments,too-few-public-methods
        self,
        strategy: Strategy,
        target: Optional[str] = None,
        json: Optional[str] = None,
        zip: Optional[str] = None,  # pylint: disable=redefined-builtin
        zip_type: Optional[str] = None,
    ):

        if not self._export_path.exists():
            self._export_path.mkdir(parents=True)

        exports: List[Export] = []
        if target is None:
            if strategy == Strategy.MostDerived:
                exports = self._export_most_derived()
            elif strategy == Strategy.OneFile:
                exports = self._export_all()
            elif strategy == Strategy.LocalImport:
                exports = self._export_with_import()
        else:
            contracts = self._compilation_unit.get_contract_from_name(target)
            if len(contracts) == 0:
                logger.error(f"{target} not found")
                return
            exports = []
            for contract in contracts:
                exports.append(self._export_contract_with_inheritance(contract))

        if json:
            export_as_json(exports, json)

        elif zip:
            save_to_zip(exports, zip, zip_type)

        else:
            save_to_disk(exports)
