import re
import logging
from slither.slithir.operations import Send, Transfer, OperationWithLValue, HighLevelCall, LowLevelCall, \
    InternalCall, InternalDynamicCall
from slither.core.declarations import Modifier
from slither.core.solidity_types import UserDefinedType, MappingType
from slither.core.declarations import Enum, Contract, Structure
from slither.core.solidity_types.elementary_type import ElementaryTypeName
from ..exceptions import FormatError, FormatImpossible
from ..utils.patches import create_patch

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('Slither.Format')

def format(slither, result):
    elements = result['elements']
    for element in elements:
        target = element['additional_fields']['target']

        convention = element['additional_fields']['convention']

        if convention == "l_O_I_should_not_be_used":
            # l_O_I_should_not_be_used cannot be automatically patched
            logger.info(f'The following naming convention cannot be patched: \n{result["description"]}')
            continue

        _patch(slither, result, element, target)

# endregion
###################################################################################
###################################################################################
# region Conventions
###################################################################################
###################################################################################

KEY = 'ALL_NAMES_USED'

# https://solidity.readthedocs.io/en/v0.5.11/miscellaneous.html#reserved-keywords
SOLIDITY_KEYWORDS = ['abstract', 'after', 'alias', 'apply', 'auto', 'case', 'catch', 'copyof', 'default', 'define',
                     'final', 'immutable', 'implements', 'in', 'inline', 'let', 'macro', 'match', 'mutable', 'null',
                     'of', 'override', 'partial', 'promise', 'reference', 'relocatable', 'sealed', 'sizeof', 'static',
                     'supports', 'switch', 'try', 'typedef', 'typeof', 'unchecked']

# https://solidity.readthedocs.io/en/v0.5.11/miscellaneous.html#language-grammar
SOLIDITY_KEYWORDS += ['pragma', 'import', 'contract', 'library', 'contract', 'function', 'using', 'struct', 'enum',
                      'public', 'private', 'internal', 'external', 'calldata', 'memory', 'modifier', 'view', 'pure',
                      'constant', 'storage', 'for', 'if', 'while', 'break', 'return', 'throw', 'else', 'type']

SOLIDITY_KEYWORDS += ElementaryTypeName

def _name_already_use(slither, name):
    # Do not convert to a name used somewhere else
    if not KEY in slither.context:
        all_names = set()
        for contract in slither.contracts_derived:
            all_names = all_names.union(set([st.name for st in contract.structures]))
            all_names = all_names.union(set([f.name for f in contract.functions_and_modifiers]))
            all_names = all_names.union(set([e.name for e in contract.enums]))
            all_names = all_names.union(set([s.name for s in contract.state_variables]))

            for function in contract.functions:
                all_names = all_names.union(set([v.name for v in function.variables]))

        slither.context[KEY] = all_names
    return name in slither.context[KEY]

def _convert_CapWords(original_name, slither):
    name = original_name.capitalize()

    while '_' in name:
        offset = name.find('_')
        if len(name) > offset:
            name = name[0:offset] + name[offset+1].upper() + name[offset+1:]

    if _name_already_use(slither, name):
        raise FormatImpossible(f'{original_name} cannot be converted to {name} (already used)')

    if name in SOLIDITY_KEYWORDS:
        raise FormatImpossible(f'{original_name} cannot be converted to {name} (Solidity keyword)')
    return name

def _convert_mixedCase(original_name, slither):

    name = original_name
    while '_' in name:
        offset = name.find('_')
        if len(name) > offset:
            name = name[0:offset] + name[offset + 1].upper() + name[offset + 2:]

    name = name[0].lower() + name[1:]
    if _name_already_use(slither, name):
        raise FormatImpossible(f'{original_name} cannot be converted to {name} (already used)')
    if name in SOLIDITY_KEYWORDS:
        raise FormatImpossible(f'{original_name} cannot be converted to {name} (Solidity keyword)')
    return name

def _convert_UPPER_CASE_WITH_UNDERSCORES(name, slither):
    if _name_already_use(slither, name.upper()):
        raise FormatImpossible(f'{name} cannot be converted to {name.upper()} (already used)')
    if name.upper() in SOLIDITY_KEYWORDS:
        raise FormatImpossible(f'{name} cannot be converted to {name.upper()} (Solidity keyword)')
    return name.upper()

conventions ={
    "CapWords":_convert_CapWords,
    "mixedCase":_convert_mixedCase,
    "UPPER_CASE_WITH_UNDERSCORES":_convert_UPPER_CASE_WITH_UNDERSCORES
}


# endregion
###################################################################################
###################################################################################
# region Helpers
###################################################################################
###################################################################################

def _get_from_contract(slither, element, name, getter):
    contract_name = element['type_specific_fields']['parent']['name']
    contract = slither.get_contract_from_name(contract_name)
    return getattr(contract, getter)(name)

# endregion
###################################################################################
###################################################################################
# region Patch dispatcher
###################################################################################
###################################################################################

def _patch(slither, result, element, _target):

    if _target == "contract":
        target = slither.get_contract_from_name(element['name'])

    elif _target == "structure":
        target = _get_from_contract(slither, element, element['name'], 'get_structure_from_name')

    elif _target == "event":
        target = _get_from_contract(slither, element, element['name'], 'get_event_from_name')

    elif _target == "function":
        # Avoid constructor (FP?)
        if element['name'] != element['type_specific_fields']['parent']['name']:
            function_sig = element['type_specific_fields']['signature']
            target = _get_from_contract(slither, element, function_sig, 'get_function_from_signature')

    elif _target == "modifier":
        modifier_sig = element['type_specific_fields']['signature']
        target = _get_from_contract(slither, element, modifier_sig, 'get_modifier_from_signature')

    elif _target == "parameter":
        contract_name = element['type_specific_fields']['parent']['type_specific_fields']['parent']['name']
        function_sig = element['type_specific_fields']['parent']['type_specific_fields']['signature']
        param_name = element['name']
        contract = slither.get_contract_from_name(contract_name)
        function = contract.get_function_from_signature(function_sig)
        target = function.get_local_variable_from_name(param_name)

    elif _target in ["variable", "variable_constant"]:
        # Local variable
        if element['type_specific_fields']['parent'] == 'function':
            contract_name = element['type_specific_fields']['parent']['type_specific_fields']['parent']['name']
            function_sig = element['type_specific_fields']['parent']['type_specific_fields']['signature']
            var_name = element['name']
            contract = slither.get_contract_from_name(contract_name)
            function = contract.get_function_from_signature(function_sig)
            target = function.get_local_variable_from_name(var_name)
        # State variable
        else:
            target = _get_from_contract(slither, element, element['name'], 'get_state_variable_from_name')

    elif _target == "enum":
        target = _get_from_contract(slither, element, element['name'], 'get_enum_from_canonical_name')

    else:
        raise FormatError("Unknown naming convention! " + _target)

    _explore(slither,
             result,
             target,
             conventions[element['additional_fields']['convention']])


# endregion
###################################################################################
###################################################################################
# region Explore functions
###################################################################################
###################################################################################

# group 1: beginning of the from type
# group 2: beginning of the to type
# nested mapping are within the group 1
#RE_MAPPING = '[ ]*mapping[ ]*\([ ]*([\=\>\(\) a-zA-Z0-9\._\[\]]*)[ ]*=>[ ]*([a-zA-Z0-9\._\[\]]*)\)'
RE_MAPPING_FROM = '([a-zA-Z0-9\._\[\]]*)'
RE_MAPPING_TO = '([\=\>\(\) a-zA-Z0-9\._\[\]\   ]*)'
RE_MAPPING = '[ ]*mapping[ ]*\([ ]*' + RE_MAPPING_FROM + '[ ]*' + '=>' + '[ ]*'+ RE_MAPPING_TO + '\)'

def _explore_type(slither, result, target, convert, type, filename_source_code, start, end):
    if isinstance(type, UserDefinedType):
        # Patch type based on contract/enum
        if isinstance(type.type, (Enum, Contract)):
            if type.type == target:
                old_str = type.type.name
                new_str = convert(old_str, slither)

                loc_start = start
                loc_end = loc_start + len(old_str)

                create_patch(result,
                             filename_source_code,
                             loc_start,
                             loc_end,
                             old_str,
                             new_str)


        else:
            # Patch type based on structure
            assert isinstance(type.type, Structure)
            if type.type == target:
                old_str = type.type.name
                new_str = convert(old_str, slither)

                loc_start = start
                loc_end = loc_start + len(old_str)

                create_patch(result,
                             filename_source_code,
                             loc_start,
                             loc_end,
                             old_str,
                             new_str)

            # Structure contain a list of elements, that might need patching
            # .elems return a list of VariableStructure
            _explore_variables_declaration(slither,
                                           type.type.elems.values(),
                                           result,
                                           target,
                                           convert)

    if isinstance(type, MappingType):
        # Mapping has three steps:
        # Convert the "from" type
        # Convert the "to" type
        # Convert nested type in the "to"
        # Ex: mapping (mapping (badName => uint) => uint)

        # Do the comparison twice, so we can factor together the re matching
        # mapping can only have elementary type in type_from
        if isinstance(type.type_to, (UserDefinedType, MappingType)) or target in [type.type_from, type.type_to]:

            full_txt_start = start
            full_txt_end = end
            full_txt = slither.source_code[filename_source_code][full_txt_start:full_txt_end]
            re_match = re.match(RE_MAPPING, full_txt)
            assert re_match

            if type.type_from == target:
                old_str = type.type_from.name
                new_str = convert(old_str, slither)

                loc_start = start + re_match.start(1)
                loc_end = loc_start + len(old_str)

                create_patch(result,
                             filename_source_code,
                             loc_start,
                             loc_end,
                             old_str,
                             new_str)

            if type.type_to == target:

                old_str = type.type_to.name
                new_str = convert(old_str, slither)

                loc_start = start + re_match.start(2)
                loc_end = loc_start + len(old_str)

                create_patch(result,
                             filename_source_code,
                             loc_start,
                             loc_end,
                             old_str,
                             new_str)

            if isinstance(type.type_to, (UserDefinedType, MappingType)):
                loc_start = start + re_match.start(2)
                loc_end = start + re_match.end(2)
                _explore_type(slither,
                              result,
                              target,
                              convert,
                              type.type_to,
                              filename_source_code,
                              loc_start,
                              loc_end)



def _explore_variables_declaration(slither, variables, result, target, convert):
    for variable in variables:
        # First explore the type of the variable
        filename_source_code = variable.source_mapping['filename_absolute']
        full_txt_start = variable.source_mapping['start']
        full_txt_end = full_txt_start + variable.source_mapping['length']
        full_txt = slither.source_code[filename_source_code][full_txt_start:full_txt_end]

        _explore_type(slither,
                      result,
                      target,
                      convert,
                      variable.type,
                      filename_source_code,
                      full_txt_start,
                      variable.source_mapping['start'] + variable.source_mapping['length'])

        # If the variable is the target
        if variable == target:
            old_str = variable.name
            new_str = convert(old_str, slither)

            # The name is after the space
            # We take all the space, as we dont know the type
            # In comparison to other matches, it is ok as there will not be more than one
            # 'spaces' zone (ex: for function, the body and the signature will also contain space)
            matches = re.finditer('[ ]*', full_txt)
            # Look for the end offset of the largest list of ' '
            loc_start = full_txt_start + max(matches, key=lambda x:len(x.group())).end()
            loc_end = loc_start + len(old_str)

            create_patch(result,
                         filename_source_code,
                         loc_start,
                         loc_end,
                         old_str,
                         new_str)


def _explore_modifiers_calls(slither, function, result, target, convert):
    for modifier in function.modifiers_statements:
        for node in modifier.nodes:
            if node.irs:
                _explore_irs(slither, node.irs, result, target, convert)
    for modifier in function.explicit_base_constructor_calls_statements:
        for node in modifier.nodes:
            if node.irs:
                _explore_irs(slither, node.irs, result, target, convert)

def _explore_structures_declaration(slither, structures, result, target, convert):
    for st in structures:
        # Explore the variable declared within the structure (VariableStructure)
        _explore_variables_declaration(slither, st.elems.values(), result, target, convert)

        # If the structure is the target
        if st == target:
            old_str = st.name
            new_str = convert(old_str, slither)

            filename_source_code = st.source_mapping['filename_absolute']
            full_txt_start = st.source_mapping['start']
            full_txt_end = full_txt_start + st.source_mapping['length']
            full_txt = slither.source_code[filename_source_code][full_txt_start:full_txt_end]

            # The name is after the space
            matches = re.finditer('struct[ ]*', full_txt)
            # Look for the end offset of the largest list of ' '
            loc_start = full_txt_start + max(matches, key=lambda x: len(x.group())).end()
            loc_end = loc_start + len(old_str)

            create_patch(result,
                         filename_source_code,
                         loc_start,
                         loc_end,
                         old_str,
                         new_str)


def _explore_events_declaration(slither, events, result, target, convert):
    for event in events:
        # Explore the parameters
        _explore_variables_declaration(slither, event.elems, result, target, convert)

        # If the event is the target
        if event == target:
            filename_source_code = event.source_mapping['filename_absolute']

            old_str = event.name
            new_str = convert(old_str, slither)

            loc_start = event.source_mapping['start']
            loc_end = loc_start + len(old_str)

            create_patch(result,
                         filename_source_code,
                         loc_start,
                         loc_end,
                         old_str,
                         new_str)

def get_ir_variables(ir):
    vars = ir.read

    if isinstance(ir, (InternalCall, InternalDynamicCall, HighLevelCall)):
        vars += [ir.function]

    if isinstance(ir, (HighLevelCall, Send, LowLevelCall, Transfer)):
        vars += [ir.call_value]

    if isinstance(ir, (HighLevelCall, LowLevelCall)):
        vars += [ir.call_gas]

    if isinstance(ir, OperationWithLValue):
        vars += [ir.lvalue]

    return [v for v in vars if v]

def _explore_irs(slither, irs, result, target, convert):
    if irs is None:
        return
    for ir in irs:
        for v in get_ir_variables(ir):
            if target == v:
                source_mapping = ir.expression.source_mapping
                filename_source_code = source_mapping['filename_absolute']
                full_txt_start = source_mapping['start']
                full_txt_end = full_txt_start + source_mapping['length']
                full_txt = slither.source_code[filename_source_code][full_txt_start:full_txt_end]

                if not str(target) in full_txt:
                    raise FormatError(f'{target} not found in {full_txt} ({source_mapping}')

                old_str = str(target)
                new_str = convert(old_str, slither)

                counter = 0
                # Can be found multiple time on the same IR
                # We patch one by one
                while old_str in full_txt:

                    target_found_at = full_txt.find((old_str))

                    full_txt = full_txt[target_found_at+1:]
                    counter += target_found_at

                    loc_start = full_txt_start + counter
                    loc_end = loc_start + len(old_str)

                    create_patch(result,
                                 filename_source_code,
                                 loc_start,
                                 loc_end,
                                 old_str,
                                 new_str)


def _explore_functions(slither, functions, result, target, convert):
    for function in functions:
        _explore_variables_declaration(slither, function.variables, result, target, convert)
        _explore_modifiers_calls(slither, function, result, target, convert)
        _explore_irs(slither, function.all_slithir_operations(), result, target, convert)

        if function == target:
            old_str = function.name
            new_str = convert(old_str, slither)

            filename_source_code = function.source_mapping['filename_absolute']
            full_txt_start = function.source_mapping['start']
            full_txt_end = full_txt_start + function.source_mapping['length']
            full_txt = slither.source_code[filename_source_code][full_txt_start:full_txt_end]

            # The name is after the space
            if isinstance(target, Modifier):
                matches = re.finditer('modifier([ ]*)', full_txt)
            else:
                matches = re.finditer('function([ ]*)', full_txt)
            # Look for the end offset of the largest list of ' '
            loc_start = full_txt_start + max(matches, key=lambda x: len(x.group())).end()
            loc_end = loc_start + len(old_str)

            create_patch(result,
                         filename_source_code,
                         loc_start,
                         loc_end,
                         old_str,
                         new_str)

def _explore_enums(slither, enums, result, target, convert):
    for enum in enums:
        if enum == target:
            print(target)
            old_str = enum.name
            new_str = convert(old_str, slither)

            filename_source_code = enum.source_mapping['filename_absolute']
            full_txt_start = enum.source_mapping['start']
            full_txt_end = full_txt_start + enum.source_mapping['length']
            full_txt = slither.source_code[filename_source_code][full_txt_start:full_txt_end]

            # The name is after the space
            matches = re.finditer('enum([ ]*)', full_txt)
            # Look for the end offset of the largest list of ' '
            loc_start = full_txt_start + max(matches, key=lambda x: len(x.group())).end()
            loc_end = loc_start + len(old_str)

            create_patch(result,
                         filename_source_code,
                         loc_start,
                         loc_end,
                         old_str,
                         new_str)


def _explore_contract(slither, contract, result, target, convert):
    _explore_variables_declaration(slither, contract.state_variables, result, target, convert)
    _explore_structures_declaration(slither, contract.structures, result, target, convert)
    _explore_functions(slither, contract.functions_and_modifiers, result, target, convert)
    _explore_enums(slither, contract.enums, result, target, convert)

    if contract == target:
        filename_source_code = contract.source_mapping['filename_absolute']
        full_txt_start = contract.source_mapping['start']
        full_txt_end = full_txt_start + contract.source_mapping['length']
        full_txt = slither.source_code[filename_source_code][full_txt_start:full_txt_end]

        old_str = contract.name
        new_str = convert(old_str, slither)

        # The name is after the space
        matches = re.finditer('contract[ ]*', full_txt)
        # Look for the end offset of the largest list of ' '
        loc_start = full_txt_start + max(matches, key=lambda x: len(x.group())).end()

        loc_end = loc_start + len(old_str)

        create_patch(result,
                     filename_source_code,
                     loc_start,
                     loc_end,
                     old_str,
                     new_str)


def _explore(slither, result, target, convert):
    for contract in slither.contracts_derived:
        _explore_contract(slither, contract, result, target, convert)




# endregion


