import logging

from slither.core.solidity_types.elementary_type import ElementaryType, ElementaryTypeName
from slither.core.solidity_types.user_defined_type import UserDefinedType
from slither.core.solidity_types.array_type import ArrayType
from slither.core.solidity_types.mapping_type import MappingType
from slither.core.solidity_types.function_type import FunctionType

from slither.core.variables.function_type_variable import FunctionTypeVariable

from slither.core.declarations.contract import Contract
from slither.core.declarations.function import Function

from slither.core.expressions.literal import Literal

import re

logger = logging.getLogger('TypeParsing')

class UnknownType:
    def __init__(self, name):
        self._name = name

    @property
    def name(self):
        return self._name

def _find_from_type_name(name, contract, contracts, structures, enums):
    name_elementary = name.split(' ')[0]
    if '[' in name_elementary:
        name_elementary = name_elementary[0:name_elementary.find('[')]
    if name_elementary in ElementaryTypeName:
        depth = name.count('[')
        if depth:
            return ArrayType(ElementaryType(name_elementary), Literal(depth))
        else:
            return ElementaryType(name_elementary)
    # We first look for contract
    # To avoid collision 
    # Ex: a structure with the name of a contract
    name_contract = name
    if name_contract.startswith('contract '):
        name_contract = name_contract[len('contract '):]
    if name_contract.startswith('library '):
        name_contract = name_contract[len('library '):]
    var_type = next((c for c in contracts if c.name == name_contract), None)

    if not var_type:
        var_type = next((st for st in structures if st.name == name), None)
    if not var_type:
        var_type = next((e for e in enums if e.name == name), None)
    if not var_type:
        # any contract can refer to another contract's enum
        enum_name = name
        if enum_name.startswith('enum '):
            enum_name = enum_name[len('enum '):]
        all_enums = [c.enums for c in contracts]
        all_enums = [item for sublist in all_enums for item in sublist]
        var_type = next((e for e in all_enums if e.name == enum_name), None)
        if not var_type:
            var_type = next((e for e in all_enums if  e.contract.name+"."+e.name == enum_name), None)
    if not var_type:
        # any contract can refer to another contract's structure
        name_struct = name
        if name_struct.startswith('struct '):
            name_struct = name_struct[len('struct '):]
            name_struct = name_struct.split(' ')[0] # remove stuff like storage pointer at the end
        all_structures = [c.structures for c in contracts]
        all_structures = [item for sublist in all_structures for item in sublist]
        var_type = next((st for st in all_structures if st.name == name_struct), None)
        if not var_type:
            var_type = next((st for st in all_structures if  st.contract.name+"."+st.name == name_struct), None)
        # case where struct xxx.xx[] where not well formed in the AST
        if not var_type:
            depth = 0
            while name_struct.endswith('[]'):
                name_struct = name_struct[0:-2]
                depth+=1
            var_type = next((st for st in all_structures if st.contract.name+"."+st.name == name_struct), None)
            if var_type:
                return ArrayType(UserDefinedType(var_type), Literal(depth))

    if not var_type:
        var_type = next((f for f in contract.functions if f.name == name), None)
    if not var_type:
        if name.startswith('function '):
            found = re.findall('function \(([ ()a-zA-Z0-9\.,]*)\) returns \(([a-zA-Z0-9\.,]*)\)', name)
            assert len(found) == 1
            params = found[0][0].split(',')
            return_values = found[0][1].split(',')
            params = [_find_from_type_name(p, contract, contracts, structures, enums) for p in params]
            return_values = [_find_from_type_name(r, contract, contracts, structures, enums) for r in return_values]
            params_vars = []
            return_vars = []
            for p in params:
               var = FunctionTypeVariable()
               var.set_type(p)
               params_vars.append(var)
            for r in return_values:
               var = FunctionTypeVariable()
               var.set_type(r)
               return_vars.append(var)
            return FunctionType(params_vars, return_vars)
    if not var_type:
        if name.startswith('mapping('):
            # nested mapping declared with var
            if name.count('mapping(') == 1 :
                found = re.findall('mapping\(([a-zA-Z0-9\.]*) => ([a-zA-Z0-9\.\[\]]*)\)', name)
            else:
                found = re.findall('mapping\(([a-zA-Z0-9\.]*) => (mapping\([=> a-zA-Z0-9\.\[\]]*\))\)', name)
            assert len(found) == 1
            from_ = found[0][0]
            to_ = found[0][1]
            
            from_type = _find_from_type_name(from_, contract, contracts, structures, enums)
            to_type = _find_from_type_name(to_, contract, contracts, structures, enums)

            return MappingType(from_type, to_type)

    if not var_type:
        logger.error('Type not found '+str(name))
        exit(-1)
    return UserDefinedType(var_type)



def parse_type(t, caller_context):
    # local import to avoid circular dependency 
    from slither.solc_parsing.expressions.expression_parsing import parse_expression
    from slither.solc_parsing.variables.function_type_variable import FunctionTypeVariableSolc

    if isinstance(caller_context, Contract):
        contract = caller_context
    elif isinstance(caller_context, Function):
        contract = caller_context.contract
    else:
        logger.error('Incorrect caller context')
        exit(-1)


    is_compact_ast = caller_context.is_compact_ast

    if is_compact_ast:
        key = 'nodeType'
    else:
        key = 'name'

    structures = contract.structures
    enums = contract.enums
    contracts = contract.slither.contracts

    if isinstance(t, UnknownType):
        return _find_from_type_name(t.name, contract, contracts, structures, enums)

    elif t[key] == 'ElementaryTypeName':
        if is_compact_ast:
            return ElementaryType(t['name'])
        return ElementaryType(t['attributes'][key])

    elif t[key] == 'UserDefinedTypeName':
        if is_compact_ast:
            return _find_from_type_name(t['typeDescriptions']['typeString'], contract, contracts, structures, enums)

        # Determine if we have a type node (otherwise we use the name node, as some older solc did not have 'type').
        type_name_key = 'type' if 'type' in t['attributes'] else key
        return _find_from_type_name(t['attributes'][type_name_key], contract, contracts, structures, enums)

    elif t[key] == 'ArrayTypeName':
        length = None
        if is_compact_ast:
            if t['length']:
                length = parse_expression(t['length'], caller_context)
            array_type = parse_type(t['baseType'], contract)
        else:
            if len(t['children']) == 2:
                length = parse_expression(t['children'][1], caller_context)
            else:
                assert len(t['children']) == 1
            array_type = parse_type(t['children'][0], contract)
        return ArrayType(array_type, length)

    elif t[key] == 'Mapping':

        if is_compact_ast:
            mappingFrom = parse_type(t['keyType'], contract)
            mappingTo = parse_type(t['valueType'], contract)
        else:
            assert len(t['children']) == 2

            mappingFrom = parse_type(t['children'][0], contract)
            mappingTo = parse_type(t['children'][1], contract)

        return MappingType(mappingFrom, mappingTo)

    elif t[key] == 'FunctionTypeName':

        if is_compact_ast:
            params = t['parameterTypes']
            return_values = t['returnParameterTypes']
            index =  'parameters'
        else:
            assert len(t['children']) == 2
            params = t['children'][0]
            return_values = t['children'][1]
            index = 'children'

        assert params[key] == 'ParameterList'
        assert return_values[key] == 'ParameterList'

        params_vars = []
        return_values_vars = []
        for p in params[index]:
            var = FunctionTypeVariableSolc(p)
            var.set_offset(p['src'], caller_context.slither)
            var.analyze(caller_context)
            params_vars.append(var)
        for p in return_values[index]:
            var = FunctionTypeVariableSolc(p)

            var.set_offset(p['src'], caller_context.slither)
            var.analyze(caller_context)
            return_values_vars.append(var)

        return FunctionType(params_vars, return_values_vars)

    logger.error('Type name not found '+str(t))
    exit(-1)
