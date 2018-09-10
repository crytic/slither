import logging

from slither.core.solidityTypes.elementaryType import ElementaryType, ElementaryTypeName
from slither.core.solidityTypes.userDefinedType import UserDefinedType
from slither.core.solidityTypes.arrayType import ArrayType
from slither.core.solidityTypes.mappingType import MappingType
from slither.core.solidityTypes.functionType import FunctionType

from slither.core.variables.functionTypeVariable import FunctionTypeVariable

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
        name_contract = name
        if name_contract.startswith('contract '):
            name_contract = name_contract[len('contract '):]
        var_type = next((c for c in contracts if c.name == name_contract), None)
    if not var_type:
        var_type = next((f for f in contract.functions if f.name == name), None)
    if not var_type:
        if name.startswith('function '):
             found = re.findall('function \(([a-zA-Z0-9\.,]*)\) returns \(([a-zA-Z0-9\.,]*)\)', name)
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
            found = re.findall('mapping\(([a-zA-Z0-9\.]*) => ([a-zA-Z0-9\.]*)\)', name)
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
    from slither.solcParsing.expressions.expressionParsing import parse_expression
    from slither.solcParsing.variables.functionTypeVariableSolc import FunctionTypeVariableSolc

    if isinstance(caller_context, Contract):
        contract = caller_context
    elif isinstance(caller_context, Function):
        contract = caller_context.contract
    else:
        logger.error('Incorrect caller context')
        exit(-1)

    structures = contract.structures
    enums = contract.enums
    contracts = contract.slither.contracts

    if isinstance(t, UnknownType):
        return _find_from_type_name(t.name, contract, contracts, structures, enums)

    elif t['name'] == 'ElementaryTypeName':
        return ElementaryType(t['attributes']['name'])

    elif t['name'] == 'UserDefinedTypeName':
        return _find_from_type_name(t['attributes']['name'], contract, contracts, structures, enums)

    elif t['name'] == 'ArrayTypeName':
        length = None
        if len(t['children']) == 2:
            length = parse_expression(t['children'][1], caller_context)
        else:
            assert len(t['children']) == 1
        array_type = parse_type(t['children'][0], contract)
        return ArrayType(array_type, length)

    elif t['name'] == 'Mapping':

        assert len(t['children']) == 2

        mappingFrom = parse_type(t['children'][0], contract)
        mappingTo = parse_type(t['children'][1], contract)

        return MappingType(mappingFrom, mappingTo)

    elif t['name'] == 'FunctionTypeName':
        assert len(t['children']) == 2

        params = t['children'][0]
        return_values = t['children'][1]

        assert params['name'] == 'ParameterList'
        assert return_values['name'] == 'ParameterList'

        params_vars = []
        return_values_vars = []
        for p in params['children']:
            var = FunctionTypeVariableSolc(p)

            var.set_offset(p['src'])
            var.analyze(caller_context)
            params_vars.append(var)
        for p in return_values['children']:
            var = FunctionTypeVariableSolc(p)

            var.set_offset(p['src'])
            var.analyze(caller_context)
            return_values_vars.append(var)

        return FunctionType(params_vars, return_values_vars)

    logger.error('Type name not found '+str(t))
    exit(-1)
