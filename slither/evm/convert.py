import logging
import sha3
import sys
from slither.core.declarations import (Contract, Function)
from slither.core.cfg.node import Node

logger = logging.getLogger('ConvertToEVM')

def get_evm_instructions(obj):
    
    assert isinstance(obj, (Function, Contract, Node))
    
    if "KEY_EVM_INS" not in obj.context:
        
        try:
            # Avoiding the addition of evm_cfg_builder as permanent dependency
            from evm_cfg_builder.cfg import CFG
        except ImportError:
            logger.error("To use evm printer, you need to install evm-cfg-builder from ToB")
            logger.error("Documentation: https://github.com/crytic/evm_cfg_builder")
            logger.error("Installation: pip install evm-cfg-builder")
            sys.exit(-1)

        slither = obj.slither

        if isinstance(obj, Node):
            contract = obj.function.contract
        elif isinstance(obj, Function):
            contract = obj.contract
        else:
            contract = obj

        # Get contract runtime bytecode, srcmap and cfg
        contract_bytecode_runtime = slither.crytic_compile.bytecode_runtime(contract.name)
        contract_srcmap_runtime = slither.crytic_compile.srcmap_runtime(contract.name)
        contract_cfg = CFG(contract_bytecode_runtime)

        # Get contract init bytecode, srcmap and cfg
        contract_bytecode_init= slither.crytic_compile.bytecode_init(contract.name)
        contract_srcmap_init = slither.crytic_compile.srcmap_init(contract.name)
        contract_cfg_init = CFG(contract_bytecode_init)

        # Get evm instructions for contract
        if isinstance(obj, Contract):
            # Combine the instructions of constructor and the rest of the contract
            obj.context["KEY_EVM_INS"] = contract_cfg_init.instructions + contract_cfg.instructions
            
        # Get evm instructions for function
        elif isinstance(obj, Function):
            
            function = obj
            
            # CFG depends on function being constructor or not
            if function.is_constructor:
                cfg = contract_cfg_init
                name = "_dispatcher"
                hash = ""
            else:
                cfg = contract_cfg
                name = function.name
                # Get first four bytes of function singature's keccak-256 hash used as function selector
                hash = "0x" + get_function_hash(function.full_name)[:8]

            function_evm = get_function_evm(cfg, name, hash)
            if function_evm == "None":
                logger.error("Function " + function.name + " not found")
                sys.exit(-1)
                
            function_ins = []
            for basic_block in sorted(function_evm.basic_blocks, key=lambda x:x.start.pc):
                for ins in basic_block.instructions:
                    function_ins.append(ins)
                    
            obj.context["KEY_EVM_INS"] = function_ins
            
        else: # Node obj
            node = obj

            # CFG and srcmap depend on function being constructor or not
            if node.function.is_constructor:
                cfg = contract_cfg_init
                srcmap = contract_srcmap_init
            else:
                cfg = contract_cfg
                srcmap = contract_srcmap_runtime
                
            # Get evm instructions for node's contract
            contract_pcs = _generate_source_to_evm_ins_mapping(cfg.instructions,
                                                               srcmap, obj.slither,
                                                               contract.source_mapping['filename_absolute'])
            contract_file = slither.source_code[contract.source_mapping['filename_absolute']].encode('utf-8')

            # Get evm instructions corresponding to node's source line number
            node_source_line = contract_file[0:node.source_mapping['start']].count("\n".encode("utf-8")) + 1
            node_pcs = contract_pcs.get(node_source_line, [])
            node_ins = []
            for pc in node_pcs:
                node_ins.append(cfg.get_instruction_at(pc))

            obj.context["KEY_EVM_INS"] = node_ins
            
    return obj.context.get("KEY_EVM_INS", [])

def get_function_hash(function_signature):
    hash = sha3.keccak_256()
    hash.update(function_signature.encode('utf-8'))
    return hash.hexdigest()

def get_function_evm(cfg, function_name, function_hash):
    for function_evm in cfg.functions:
        # Match function hash
        if function_evm.name[:2] == "0x" and function_evm.name == function_hash:
            return function_evm
        # Match function name
        elif function_evm.name[:2] != "0x" and function_evm.name.split('(')[0] == function_name:
            return function_evm
    return "None"

def _generate_source_to_evm_ins_mapping(evm_instructions, srcmap_runtime, slither, filename):
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
        # In order to compress these source mappings especially for bytecode, the following rules are used:
        # If a field is empty, the value of the preceding element is used.
        # If a : is missing, all following fields are considered empty.

        mapping_item = mapping.split(':')
        mapping_item += prev_mapping[len(mapping_item):]

        for i in range(len(mapping_item)):
            if mapping_item[i] == '':
                mapping_item[i] = int(prev_mapping[i])

        offset, length, file_id, _ = mapping_item
        prev_mapping = mapping_item

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

    return(source_to_evm_mapping)
