"""
    Module printing evm mapping of the contract
"""

import logging
from slither.printers.abstract_printer import AbstractPrinter
try:
    # Avoiding the addition of evm_cfg_builder as permanent dependency
    from evm_cfg_builder.cfg import CFG
except ImportError:
    logger.error("To use evm printer, you need to install evm-cfg-builder from ToB")
    logger.error("Documentation: https://github.com/crytic/evm_cfg_builder")
    logger.error("Installation: pip install evm-cfg-builder")
    sys.exit(-1)

    
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

        evm_info = self._extract_evm_info(self.slither)

        for contract in self.slither.contracts_derived:
            print('Contract {}'.format(contract.name))
            
            contract_file = self.slither.source_code[contract.source_mapping['filename_absolute']].encode('utf-8')
            contract_file_lines = open(contract.source_mapping['filename_absolute'],'r').readlines()
            contract_cfg = evm_info['cfg', contract.name]
            contract_pcs = evm_info['mapping', contract.name]

            for function in contract.functions:
                print(f'\tFunction {function.canonical_name}')
                for node in function.nodes:
                    print("\t\tNode: " + str(node))
                    node_source_line = contract_file[0:node.source_mapping['start']].count("\n".encode("utf-8")) + 1
                    print('\t\tSource line {}: {}'.format(node_source_line, contract_file_lines[node_source_line-1].rstrip()))
                    print('\t\tEVM Instructions:')
                    node_pcs = contract_pcs.get(node_source_line, [])
                    for pc in node_pcs:
                        print('\t\t\t0x{:x}: {}'.format(int(pc), contract_cfg.get_instruction_at(pc)))
                        
            for modifier in contract.modifiers:
                print(f'\tModifier {modifier.canonical_name}')
                for node in modifier.nodes:
                    node_source_line = contract_file[0:node.source_mapping['start']].count("\n".encode("utf-8")) + 1
                    print('\t\tSource line {}: {}'.format(node_source_line, contract_file_lines[node_source_line-1].rstrip()))
                    print('\t\tEVM Instructions:')
                    node_pcs = contract_pcs.get(node_source_line, [])
                    for pc in node_pcs:
                        print('\t\t\t0x{:x}: {}'.format(int(pc), contract_cfg.get_instruction_at(pc)))

                        
    def _extract_evm_info(self, slither):
        """
        Extract evm information for all derived contracts using evm_cfg_builder

        Returns: evm CFG and Solidity source to Program Counter (pc) mapping
        """
        
        evm_info = {}
        
        for contract in slither.contracts_derived:
            contract_bytecode_runtime = slither.crytic_compile.bytecode_runtime(contract.name)
            contract_srcmap_runtime = slither.crytic_compile.srcmap_runtime(contract.name)
            cfg = CFG(contract_bytecode_runtime)
            evm_info['cfg', contract.name] = cfg
            evm_info['mapping', contract.name] = self._generate_source_to_evm_ins_mapping(cfg.instructions,
                                                                                 contract_srcmap_runtime, slither,
                                                                                 contract.source_mapping['filename_absolute'])
        return(evm_info)

    
    def _generate_source_to_evm_ins_mapping(self, evm_instructions, srcmap_runtime, slither, filename):
        """
        Generate Solidity source to EVM instruction mapping using evm_cfg_builder:cfg.instructions and solc:srcmap_runtime

        Returns: Solidity source to EVM instruction mapping
        """
        
        source_to_evm_mapping = {}
        file_source = slither.source_code[filename].encode('utf-8')
        prev_mapping = []
        
        for idx, mapping in enumerate(srcmap_runtime):
            # Parse srcmap_runtime according to its format
            # See https://solidity.readthedocs.io/en/v0.5.9/miscellaneous.html#source-mappings
            
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
            
            # Append evm instructions to the corresponding source line number
            # Note: Some evm instructions in mapping are not necessarily in program execution order
            # Note: The order depends on how solc creates the srcmap_runtime
            source_to_evm_mapping.setdefault(line_number, []).append(evm_instructions[idx].pc)
            
            prev_mapping = mapping_item
            
        return(source_to_evm_mapping)
