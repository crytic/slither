import logging
import sys
from slither.core.declarations import (Contract, Function)
from slither.core.cfg.node import Node
from slither.utils.function import get_function_id
from .evm_cfg_builder import load_evm_cfg_builder

logger = logging.getLogger('ConvertToEVM')

KEY_EVM_INS = "EVM_INSTRUCTIONS"

def get_evm_instructions (obj):

    assert isinstance(obj, (Function, Contract, Node))

    if KEY_EVM_INS not in obj.context:

        CFG = load_evm_cfg_builder()

        slither = obj.slither

        contract_info = {}
        function_info = {}
        node_info = {}

        if isinstance(obj, Node):
            contract_info['contract'] = obj.function.contract
        elif isinstance(obj, Function):
            contract_info['contract'] = obj.contract
        else:
            contract_info['contract'] = obj

        # Get contract runtime bytecode, srcmap and cfg
        contract_info['bytecode_runtime'] = slither.crytic_compile.bytecode_runtime(
            contract_info['contract'].name)
        contract_info['srcmap_runtime'] = slither.crytic_compile.srcmap_runtime(
            contract_info['contract'].name)
        contract_info['cfg'] = CFG(contract_info['bytecode_runtime'])

        # Get contract init bytecode, srcmap and cfg
        contract_info['bytecode_init']= slither.crytic_compile.bytecode_init(contract_info['contract'].name)
        contract_info['srcmap_init'] = slither.crytic_compile.srcmap_init(contract_info['contract'].name)
        contract_info['cfg_init'] = CFG(contract_info['bytecode_init'])

        # Get evm instructions
        if isinstance(obj, Contract):
            # Get evm instructions for contract
            obj.context[KEY_EVM_INS] = _get_evm_instructions_contract(contract_info)

        elif isinstance(obj, Function):
            # Get evm instructions for function
            function_info['function'] = obj
            function_info['contract_info'] = contract_info
            obj.context[KEY_EVM_INS] = _get_evm_instructions_function(function_info)

        else:
            # Get evm instructions for node
            node_info['node'] = obj

            # CFG and srcmap depend on function being constructor or not
            if node_info['node'].function.is_constructor:
                cfg = contract_info['cfg_init']
                srcmap = contract_info['srcmap_init']
            else:
                cfg = contract_info['cfg']
                srcmap = contract_info['srcmap_runtime']

            node_info['cfg'] = cfg
            node_info['srcmap'] = srcmap
            node_info['contract'] = contract_info['contract']
            node_info['slither'] = slither

            obj.context[KEY_EVM_INS] = _get_evm_instructions_node(node_info)

    return obj.context.get(KEY_EVM_INS, [])


def _get_evm_instructions_contract (contract_info):

    # Combine the instructions of constructor and the rest of the contract
    return contract_info['cfg_init'].instructions + contract_info['cfg'].instructions


def _get_evm_instructions_function (function_info):

            function = function_info['function']

            # CFG depends on function being constructor or not
            if function.is_constructor:
                cfg = function_info['contract_info']['cfg_init']
                # _dispatcher is the only function recognised by evm-cfg-builder in bytecode_init.
                # _dispatcher serves the role of the constructor in init code,
                #    given that there are no other functions.
                # Todo: Could rename it appropriately in evm-cfg-builder
                #    by detecting that init bytecode is being parsed.
                name = "_dispatcher"
                hash = ""
            else:
                cfg = function_info['contract_info']['cfg']
                name = function.name
                # Get first four bytes of function singature's keccak-256 hash used as function selector
                hash = str(hex(get_function_id(function.full_name)))

            function_evm = _get_function_evm(cfg, name, hash)
            if function_evm == "None":
                logger.error("Function " + function.name + " not found")
                sys.exit(-1)

            function_ins = []
            for basic_block in sorted(function_evm.basic_blocks, key=lambda x:x.start.pc):
                for ins in basic_block.instructions:
                    function_ins.append(ins)

            return function_ins


def _get_evm_instructions_node (node_info):
    # Get evm instructions for node's contract
    contract_pcs = generate_source_to_evm_ins_mapping(node_info['cfg'].instructions,
                                                                  node_info['srcmap'],
                                                                  node_info['slither'],
                                                                  node_info['contract'].source_mapping['filename_absolute'])
    contract_file = node_info['slither'].source_code[node_info['contract'].source_mapping['filename_absolute']].encode('utf-8')

    # Get evm instructions corresponding to node's source line number
    node_source_line = contract_file[0:node_info['node'].source_mapping['start']].count("\n".encode("utf-8"))\
    + 1
    node_pcs = contract_pcs.get(node_source_line, [])
    node_ins = []
    for pc in node_pcs:
        node_ins.append(node_info['cfg'].get_instruction_at(pc))

    return node_ins


def _get_function_evm(cfg, function_name, function_hash):
    for function_evm in cfg.functions:
        # Match function hash
        if function_evm.name[:2] == "0x" and function_evm.name == function_hash:
            return function_evm
        # Match function name
        elif function_evm.name[:2] != "0x" and function_evm.name.split('(')[0] == function_name:
            return function_evm
    return "None"


def generate_source_to_evm_ins_mapping(evm_instructions, srcmap_runtime, slither, filename):
    """
    Generate Solidity source to EVM instruction mapping using evm_cfg_builder:cfg.instructions 
    and solc:srcmap_runtime

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
