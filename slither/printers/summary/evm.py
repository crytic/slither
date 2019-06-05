"""
    Module printing evm mapping of the contract
"""

import logging
try:
    from evm_cfg_builder.cfg import CFG
except ImportError:
    logger.error("ERROR: in order to use evm printer, you need to install evm-cfg-builder")
    logger.error("pip install evm-cfg-builder")
    sys.exit(-1)
from slither.printers.abstract_printer import AbstractPrinter
from slither.utils.colors import blue, green, magenta

class PrinterEVM(AbstractPrinter):

    ARGUMENT = 'evm'
    HELP = 'Print the evm instructions of nodes in functions'

    WIKI = 'https://github.com/trailofbits/slither/wiki/Printer-documentation#evm'

    def output(self, _filename):
        """
            _filename is not used
            Args:
                _filename(string)
        """

        source_to_pc_mapping = self._process_evm_cfg(self.slither)

        for contract in self.slither.contracts_derived:
            print('Contract {}'.format(contract.name))
            contract_file = self.slither.source_code[contract.source_mapping['filename_absolute']].encode('utf-8')
            contract_file_lines = open(contract.source_mapping['filename_absolute'],'r').readlines()
            contract_pcs = source_to_pc_mapping['mapping', contract.name]
            contract_cfg = source_to_pc_mapping['cfg', contract.name]
            for function in contract.functions:
                print(f'\tFunction {function.canonical_name}')
                for node in function.nodes:
                    print("\t\tNode: " + str(node))
                    node_source_line = contract_file[0:node.source_mapping['start']].count("\n".encode("utf-8")) + 1
                    print('\t\tSource line {}: {}'.format(node_source_line, contract_file_lines[node_source_line-1].rstrip()))
                    print('\t\tEVM Instructions:')
                    node_pcs = contract_pcs.get(node_source_line, "[]")
                    for pc in node_pcs:
                        print('\t\t\t{}'.format(contract_cfg.get_instruction_at(pc)))
            for modifier in contract.modifiers:
                print('\tModifier {}'.format(modifier.canonical_name))
                for node in modifier.nodes:
                    node_source_line = contract_file[0:node.source_mapping['start']].count("\n".encode("utf-8")) + 1
                    print('\t\tSource line {}: {}'.format(node_source_line, contract_file_lines[node_source_line-1].rstrip()))
                    print('\t\tEVM Instructions:')
                    node_pcs = contract_pcs[node_source_line]
                    for pc in node_pcs:
                        print('\t\t\t{}'.format(contract_cfg.get_instruction_at(pc)))

    def _process_evm_cfg(self, slither):
        source_to_pc_mapping = {}
        for contract in slither.contracts_derived:
            contract_bytecode_runtime = slither.crytic_compile.bytecode_runtime(contract.name)
            contract_srcmap_runtime = slither.crytic_compile.srcmap_runtime(contract.name)
            cfg = CFG(contract_bytecode_runtime)
            source_to_pc_mapping['cfg', contract.name] = cfg
            source_to_pc_mapping['mapping', contract.name] = self._generate_source_to_ins_mapping(cfg.instructions,
                                                                                 contract_srcmap_runtime, slither,
                                                                                 contract.source_mapping['filename_absolute'])
        return(source_to_pc_mapping)
    
    def _generate_source_to_ins_mapping(self, evm_instructions, srcmap_runtime, slither, filename):
        source_to_pc_mapping = {}
        file_source = slither.source_code[filename].encode('utf-8')
        prev_mapping = []
        for idx, mapping in enumerate(srcmap_runtime):
            mapping_item = mapping.split(':')
            mapping_item += prev_mapping[len(mapping_item):]
            for i in range(len(mapping_item)):
                if mapping_item[i] == '':
                    mapping_item[i] = int(prev_mapping[i])
            offset, length, file_id, _ = mapping_item
            if file_id == '-1':
                # Internal compiler-generated code snippets to be ignored
                # See https://github.com/ethereum/solidity/issues/6119#issuecomment-467797635
                continue
            offset = int(offset)
            line_number = file_source[0:offset].count("\n".encode("utf-8")) + 1
            prev_mapping = mapping_item
            source_to_pc_mapping.setdefault(line_number, []).append(evm_instructions[idx].pc)
        return(source_to_pc_mapping)
