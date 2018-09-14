"""
    Utils module
"""
import re

def find_call(call, contract, contracts):
    """ Find call in the contract

    Do not respect c3 lineralization
    Args:
        call: call the find
        contract: current contract
        contracts: list of contracts
    Return:
    function: returns the function called (or None if the funciton was not found)
"""
    if '.call.value' in str(call):
        return None
    if '.call.gas.value' in str(call):
        return None
    for f in contract.functions + contract.modifiers:
        if call == f.name:
            return f
    for father in contract.inheritance:
        fatherContract = next((x for x in contracts if x.name == father), None)
        if fatherContract:
            for f in fatherContract.functions:
                if call == f.name:
                    return f
            call_found = find_call(call, fatherContract, contracts)
            if call_found:
                return call_found
    return None

def convert_offset(offset, sourceUnits):
    '''
    Convert a text offset to a real offset
    see https://solidity.readthedocs.io/en/develop/miscellaneous.html#source-mappings

    To handle solc <0.3.6:
      - If the matching is not found, returns an empty dict
      - If the matching is found, but the filename is not knwon, return only start/length
    Args:
        offset (str): format: '..:..:..'
        sourceUnits (dict): map int -> filename
    Returns:
        (dict): {'start':0, 'length':0, 'filename': 'file.sol'}
    '''
    position = re.findall('([0-9]*):([0-9]*):([-]?[0-9]*)', offset)
    if len(position) != 1:
        return {}

    s, l, f = position[0]
    s = int(s)
    l = int(l)
    f = int(f)

    if f not in sourceUnits:
        return {'start':s, 'length':l}
    filename = sourceUnits[f]
    return {'start':s, 'length':l, 'filename': filename}
