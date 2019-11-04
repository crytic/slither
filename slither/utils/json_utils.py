import os
import json
import logging
from collections import OrderedDict

from slither.core.cfg.node import Node
from slither.core.declarations import Contract, Function, Enum, Event, Structure, Pragma
from slither.core.source_mapping.source_mapping import SourceMapping
from slither.core.variables.variable import Variable
from slither.exceptions import SlitherError
from slither.utils.colors import yellow

logger = logging.getLogger("Slither")


###################################################################################
###################################################################################
# region Output
###################################################################################
###################################################################################

def output_json(filename, error, results):
    """

    :param filename: Filename where the json will be written. If None or "-", write to stdout
    :param error: Error to report
    :param results: Results to report
    :param logger: Logger where to log potential info
    :return:
    """
    # Create our encapsulated JSON result.
    json_result = {
        "success": error is None,
        "error": error,
        "results": results
    }

    if filename == "-":
        filename = None

    # Determine if we should output to stdout
    if filename is None:
        # Write json to console
        print(json.dumps(json_result))
    else:
        # Write json to file
        if os.path.isfile(filename):
            logger.info(yellow(f'{filename} exists already, the overwrite is prevented'))
        else:
            with open(filename, 'w', encoding='utf8') as f:
                json.dump(json_result, f, indent=2)


# endregion
###################################################################################
###################################################################################
# region Json generation
###################################################################################
###################################################################################

def _convert_to_description(d):
    if isinstance(d, str):
        return d

    if not isinstance(d, SourceMapping):
        raise SlitherError(f'{d} does not inherit from SourceMapping, conversion impossible')

    if isinstance(d, Node):
        if d.expression:
            return f'{d.expression} ({d.source_mapping_str})'
        else:
            return f'{str(d)} ({d.source_mapping_str})'

    if hasattr(d, 'canonical_name'):
        return f'{d.canonical_name} ({d.source_mapping_str})'

    if hasattr(d, 'name'):
        return f'{d.name} ({d.source_mapping_str})'

    raise SlitherError(f'{type(d)} cannot be converted (no name, or canonical_name')

def _convert_to_markdown(d, markdown_root):
    if isinstance(d, str):
        return d

    if not isinstance(d, SourceMapping):
        raise SlitherError(f'{d} does not inherit from SourceMapping, conversion impossible')

    if isinstance(d, Node):
        if d.expression:
            return f'[{d.expression}]({d.source_mapping_to_markdown(markdown_root)})'
        else:
            return f'[{str(d)}]({d.source_mapping_to_markdown(markdown_root)})'

    if hasattr(d, 'canonical_name'):
        return f'[{d.canonical_name}]({d.source_mapping_to_markdown(markdown_root)})'

    if hasattr(d, 'name'):
        return f'[{d.name}]({d.source_mapping_to_markdown(markdown_root)})'

    raise SlitherError(f'{type(d)} cannot be converted (no name, or canonical_name')

def generate_json_result(info, additional_fields=None, markdown_root='', standard_format=False):
    if additional_fields is None:
        additional_fields = {}
    d = OrderedDict()
    d['elements'] = []
    d['description'] = ''.join(_convert_to_description(d) for d in info)
    d['markdown'] = ''.join(_convert_to_markdown(d, markdown_root) for d in info)

    if standard_format:
        to_add = [i for i in info if not isinstance(i, str)]

        for add in to_add:
            if isinstance(add, Variable):
                add_variable_to_json(add, d)
            elif isinstance(add, Contract):
                add_contract_to_json(add, d)
            elif isinstance(add, Function):
                add_function_to_json(add, d)
            elif isinstance(add, Enum):
                add_enum_to_json(add, d)
            elif isinstance(add, Event):
                add_event_to_json(add, d)
            elif isinstance(add, Structure):
                add_struct_to_json(add, d)
            elif isinstance(add, Pragma):
                add_pragma_to_json(add, d)
            elif isinstance(add, Node):
                add_node_to_json(add, d)
            else:
                raise SlitherError(f'Impossible to add {type(add)} to the json')

    if additional_fields:
        d['additional_fields'] = additional_fields

    return d


# endregion
###################################################################################
###################################################################################
# region Internal functions
###################################################################################
###################################################################################

def _create_base_element(type, name, source_mapping, type_specific_fields=None, additional_fields=None):
    if additional_fields is None:
        additional_fields = {}
    if type_specific_fields is None:
        type_specific_fields = {}
    element = {'type': type,
               'name': name,
               'source_mapping': source_mapping}
    if type_specific_fields:
        element['type_specific_fields'] = type_specific_fields
    if additional_fields:
        element['additional_fields'] = additional_fields
    return element


def _create_parent_element(element):
    from slither.core.children.child_contract import ChildContract
    from slither.core.children.child_function import ChildFunction
    from slither.core.children.child_inheritance import ChildInheritance
    if isinstance(element, ChildInheritance):
        if element.contract_declarer:
            contract = {'elements': []}
            add_contract_to_json(element.contract_declarer, contract)
            return contract['elements'][0]
    elif isinstance(element, ChildContract):
        if element.contract:
            contract = {'elements': []}
            add_contract_to_json(element.contract, contract)
            return contract['elements'][0]
    elif isinstance(element, ChildFunction):
        if element.function:
            function = {'elements': []}
            add_function_to_json(element.function, function)
            return function['elements'][0]
    return None


# endregion
###################################################################################
###################################################################################
# region Variables
###################################################################################
###################################################################################

def add_variable_to_json(variable, d, additional_fields=None):
    if additional_fields is None:
        additional_fields = {}
    type_specific_fields = {
        'parent': _create_parent_element(variable)
    }
    element = _create_base_element('variable',
                                   variable.name,
                                   variable.source_mapping,
                                   type_specific_fields,
                                   additional_fields)
    d['elements'].append(element)


def add_variables_to_json(variables, d):
    for variable in sorted(variables, key=lambda x: x.name):
        add_variable_to_json(variable, d)


# endregion
###################################################################################
###################################################################################
# region Contract
###################################################################################
###################################################################################

def add_contract_to_json(contract, d, additional_fields=None):
    if additional_fields is None:
        additional_fields = {}
    element = _create_base_element('contract',
                                   contract.name,
                                   contract.source_mapping,
                                   {},
                                   additional_fields)
    d['elements'].append(element)


# endregion
###################################################################################
###################################################################################
# region Functions
###################################################################################
###################################################################################

def add_function_to_json(function, d, additional_fields=None):
    if additional_fields is None:
        additional_fields = {}
    type_specific_fields = {
        'parent': _create_parent_element(function),
        'signature': function.full_name
    }
    element = _create_base_element('function',
                                   function.name,
                                   function.source_mapping,
                                   type_specific_fields,
                                   additional_fields)
    d['elements'].append(element)


def add_functions_to_json(functions, d, additional_fields=None):
    if additional_fields is None:
        additional_fields = {}
    for function in sorted(functions, key=lambda x: x.name):
        add_function_to_json(function, d, additional_fields)


# endregion
###################################################################################
###################################################################################
# region Enum
###################################################################################
###################################################################################


def add_enum_to_json(enum, d, additional_fields=None):
    if additional_fields is None:
        additional_fields = {}
    type_specific_fields = {
        'parent': _create_parent_element(enum)
    }
    element = _create_base_element('enum',
                                   enum.name,
                                   enum.source_mapping,
                                   type_specific_fields,
                                   additional_fields)
    d['elements'].append(element)


# endregion
###################################################################################
###################################################################################
# region Structures
###################################################################################
###################################################################################

def add_struct_to_json(struct, d, additional_fields=None):
    if additional_fields is None:
        additional_fields = {}
    type_specific_fields = {
        'parent': _create_parent_element(struct)
    }
    element = _create_base_element('struct',
                                   struct.name,
                                   struct.source_mapping,
                                   type_specific_fields,
                                   additional_fields)
    d['elements'].append(element)


# endregion
###################################################################################
###################################################################################
# region Events
###################################################################################
###################################################################################

def add_event_to_json(event, d, additional_fields=None):
    if additional_fields is None:
        additional_fields = {}
    type_specific_fields = {
        'parent': _create_parent_element(event),
        'signature': event.full_name
    }
    element = _create_base_element('event',
                                   event.name,
                                   event.source_mapping,
                                   type_specific_fields,
                                   additional_fields)

    d['elements'].append(element)


# endregion
###################################################################################
###################################################################################
# region Nodes
###################################################################################
###################################################################################

def add_node_to_json(node, d, additional_fields=None):
    if additional_fields is None:
        additional_fields = {}
    type_specific_fields = {
        'parent': _create_parent_element(node),
    }
    node_name = str(node.expression) if node.expression else ""
    element = _create_base_element('node',
                                   node_name,
                                   node.source_mapping,
                                   type_specific_fields,
                                   additional_fields)
    d['elements'].append(element)


def add_nodes_to_json(nodes, d):
    for node in sorted(nodes, key=lambda x: x.node_id):
        add_node_to_json(node, d)


# endregion
###################################################################################
###################################################################################
# region Pragma
###################################################################################
###################################################################################

def add_pragma_to_json(pragma, d, additional_fields=None):
    if additional_fields is None:
        additional_fields = {}
    type_specific_fields = {
        'directive': pragma.directive
    }
    element = _create_base_element('pragma',
                                   pragma.version,
                                   pragma.source_mapping,
                                   type_specific_fields,
                                   additional_fields)
    d['elements'].append(element)


# endregion
###################################################################################
###################################################################################
# region File
###################################################################################
###################################################################################


def add_file_to_json(filename, content, d, additional_fields=None):
    if additional_fields is None:
        additional_fields = {}
    type_specific_fields = {
        'filename': filename,
        'content': content
    }
    element = _create_base_element('file',
                                   type_specific_fields,
                                   additional_fields)

    d['elements'].append(element)


# endregion
###################################################################################
###################################################################################
# region Pretty Table
###################################################################################
###################################################################################


def add_pretty_table_to_json(content, name, d, additional_fields=None):
    if additional_fields is None:
        additional_fields = {}
    type_specific_fields = {
        'content': content,
        'name': name
    }
    element = _create_base_element('pretty_table',
                                   type_specific_fields,
                                   additional_fields)

    d['elements'].append(element)


# endregion
###################################################################################
###################################################################################
# region Others
###################################################################################
###################################################################################

def add_other_to_json(name, source_mapping, d, slither, additional_fields=None):
    # If this a tuple with (filename, start, end), convert it to a source mapping.
    if additional_fields is None:
        additional_fields = {}
    if isinstance(source_mapping, tuple):
        # Parse the source id
        (filename, start, end) = source_mapping
        source_id = next(
            (source_unit_id for (source_unit_id, source_unit_filename) in slither.source_units.items() if
             source_unit_filename == filename), -1)

        # Convert to a source mapping string
        source_mapping = f"{start}:{end}:{source_id}"

    # If this is a source mapping string, parse it.
    if isinstance(source_mapping, str):
        source_mapping_str = source_mapping
        source_mapping = SourceMapping()
        source_mapping.set_offset(source_mapping_str, slither)

    # If this is a source mapping object, get the underlying source mapping dictionary
    if isinstance(source_mapping, SourceMapping):
        source_mapping = source_mapping.source_mapping

    # Create the underlying element and add it to our resulting json
    element = _create_base_element('other',
                                   name,
                                   source_mapping,
                                   {},
                                   additional_fields)
    d['elements'].append(element)
