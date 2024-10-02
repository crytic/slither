"""
    Module printing evm mapping of the contract
"""
import logging
from typing import Union, List, Dict

from slither.printers.abstract_printer import AbstractPrinter
from slither.core.declarations.function import Function
from slither.core.declarations.modifier import Modifier
from slither.analyses.evm import (
    generate_source_to_evm_ins_mapping,
    load_evm_cfg_builder,
)
from slither.utils.colors import blue, green, magenta, red


logger: logging.Logger = logging.getLogger("EVMPrinter")


def _extract_evm_info(slither):
    """
    Extract evm information for all derived contracts using evm_cfg_builder

    Returns: evm CFG and Solidity source to Program Counter (pc) mapping
    """

    evm_info = {}

    CFG = load_evm_cfg_builder()

    for contract in slither.contracts_derived:
        contract_bytecode_runtime = contract.file_scope.bytecode_runtime(
            contract.compilation_unit.crytic_compile_compilation_unit, contract.name
        )

        if not contract_bytecode_runtime:
            logger.info(
                "Contract %s (abstract: %r) has no bytecode runtime, skipping. ",
                contract.name,
                contract.is_abstract,
            )
            evm_info["empty", contract.name] = True
            continue

        contract_srcmap_runtime = contract.file_scope.srcmap_runtime(
            contract.compilation_unit.crytic_compile_compilation_unit, contract.name
        )
        cfg = CFG(contract_bytecode_runtime)
        evm_info["cfg", contract.name] = cfg
        evm_info["mapping", contract.name] = generate_source_to_evm_ins_mapping(
            cfg.instructions,
            contract_srcmap_runtime,
            slither,
            contract.source_mapping.filename.absolute,
        )

        contract_bytecode_init = contract.file_scope.bytecode_init(
            contract.compilation_unit.crytic_compile_compilation_unit, contract.name
        )
        contract_srcmap_init = contract.file_scope.srcmap_init(
            contract.compilation_unit.crytic_compile_compilation_unit, contract.name
        )
        cfg_init = CFG(contract_bytecode_init)

        evm_info["cfg_init", contract.name] = cfg_init
        evm_info["mapping_init", contract.name] = generate_source_to_evm_ins_mapping(
            cfg_init.instructions,
            contract_srcmap_init,
            slither,
            contract.source_mapping.filename.absolute,
        )

    return evm_info


# pylint: disable=too-many-locals
class PrinterEVM(AbstractPrinter):
    ARGUMENT = "evm"
    HELP = "Print the evm instructions of nodes in functions"

    WIKI = "https://github.com/trailofbits/slither/wiki/Printer-documentation#evm"

    def build_element_node_str(
        self,
        element: Union["Modifier", "Function"],
        contract_pcs: Dict[int, List[int]],
        contract_cfg,
    ) -> str:
        element_file = self.slither.source_code[
            element.contract_declarer.source_mapping.filename.absolute
        ].splitlines()

        return_string = ""
        for node in element.nodes:
            return_string += green(f"\t\tNode: {node}\n")
            node_source_line = node.source_mapping.lines[0]
            return_string += green(
                f"\t\tSource line {node_source_line}: {element_file[node_source_line - 1].rstrip()}\n"
            )

            return_string += magenta("\t\tEVM Instructions:\n")
            node_pcs = contract_pcs.get(node_source_line, [])
            for pc in node_pcs:
                return_string += magenta(
                    f"\t\t\t{hex(pc)}: {contract_cfg.get_instruction_at(pc)}\n"
                )

        return return_string

    def output(self, _filename):
        """
        _filename is not used
        Args:
            _filename(string)
        """

        txt = ""
        if not self.slither.crytic_compile:
            txt = "The EVM printer requires to compile with crytic-compile"
            self.info(red(txt))
            res = self.generate_output(txt)
            return res
        evm_info = _extract_evm_info(self.slither)

        for contract in self.slither.contracts_derived:
            txt += blue(f"Contract {contract.name}\n")

            if evm_info.get(("empty", contract.name), False):
                txt += "\tempty contract\n"
                continue

            for function in contract.functions:
                txt += blue(f"\tFunction {function.canonical_name}\n")

                txt += self.build_element_node_str(
                    function,
                    evm_info["mapping", contract.name]
                    if not function.is_constructor
                    else evm_info["mapping_init", contract.name],
                    evm_info["cfg", contract.name]
                    if not function.is_constructor
                    else evm_info["cfg_init", contract.name],
                )

            for modifier in contract.modifiers:
                txt += blue(f"\tModifier {modifier.canonical_name}\n")

                txt += self.build_element_node_str(
                    modifier,
                    evm_info["mapping", contract.name],
                    evm_info["cfg", contract.name],
                )

        self.info(txt)
        res = self.generate_output(txt)
        return res
