"""
    Module printing evm mapping of the contract
"""
from slither.printers.abstract_printer import AbstractPrinter
from slither.analyses.evm import (
    generate_source_to_evm_ins_mapping,
    load_evm_cfg_builder,
)
from slither.utils.colors import blue, green, magenta, red


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

            contract_file = self.slither.source_code[
                contract.source_mapping.filename.absolute
            ].encode("utf-8")
            with open(contract.source_mapping.filename.absolute, "r", encoding="utf8") as f:
                contract_file_lines = f.readlines()

            contract_pcs = {}
            contract_cfg = {}

            for function in contract.functions:
                txt += blue(f"\tFunction {function.canonical_name}\n")

                # CFG and source mapping depend on function being constructor or not
                if function.is_constructor:
                    contract_cfg = evm_info["cfg_init", contract.name]
                    contract_pcs = evm_info["mapping_init", contract.name]
                else:
                    contract_cfg = evm_info["cfg", contract.name]
                    contract_pcs = evm_info["mapping", contract.name]

                for node in function.nodes:
                    txt += green("\t\tNode: " + str(node) + "\n")
                    node_source_line = (
                        contract_file[0 : node.source_mapping.start].count("\n".encode("utf-8")) + 1
                    )
                    txt += green(
                        f"\t\tSource line {node_source_line}: {contract_file_lines[node_source_line - 1].rstrip()}\n"
                    )
                    txt += magenta("\t\tEVM Instructions:\n")
                    node_pcs = contract_pcs.get(node_source_line, [])
                    for pc in node_pcs:
                        txt += magenta(f"\t\t\t{hex(pc)}: {contract_cfg.get_instruction_at(pc)}\n")

            for modifier in contract.modifiers:
                txt += blue(f"\tModifier {modifier.canonical_name}\n")
                for node in modifier.nodes:
                    txt += green("\t\tNode: " + str(node) + "\n")
                    node_source_line = (
                        contract_file[0 : node.source_mapping.start].count("\n".encode("utf-8")) + 1
                    )
                    txt += green(
                        f"\t\tSource line {node_source_line}: {contract_file_lines[node_source_line - 1].rstrip()}\n"
                    )
                    txt += magenta("\t\tEVM Instructions:\n")
                    node_pcs = contract_pcs.get(node_source_line, [])
                    for pc in node_pcs:
                        txt += magenta(f"\t\t\t{hex(pc)}: {contract_cfg.get_instruction_at(pc)}\n")

        self.info(txt)
        res = self.generate_output(txt)
        return res
