import hashlib
import os
import json
import logging
import zipfile
from collections import OrderedDict
from typing import Optional, Dict, List, Union, Any, TYPE_CHECKING
from zipfile import ZipFile

from slither.core.cfg.node import Node
from slither.core.declarations import Contract, Function, Enum, Event, Structure, Pragma
from slither.core.source_mapping.source_mapping import SourceMapping
from slither.core.variables.variable import Variable
from slither.exceptions import SlitherError
from slither.utils.colors import yellow
from slither.utils.myprettytable import MyPrettyTable

if TYPE_CHECKING:
    from slither.core.compilation_unit import SlitherCompilationUnit

logger = logging.getLogger("Slither")


###################################################################################
###################################################################################
# region Output
###################################################################################
###################################################################################


def output_to_json(filename: str, error, results: Dict):
    """

    :param filename: Filename where the json will be written. If None or "-", write to stdout
    :param error: Error to report
    :param results: Results to report
    :param logger: Logger where to log potential info
    :return:
    """
    # Create our encapsulated JSON result.
    json_result = {"success": error is None, "error": error, "results": results}

    if filename == "-":
        filename = None

    # Determine if we should output to stdout
    if filename is None:
        # Write json to console
        print(json.dumps(json_result))
    else:
        # Write json to file
        if os.path.isfile(filename):
            logger.info(yellow(f"{filename} exists already, the overwrite is prevented"))
        else:
            with open(filename, "w", encoding="utf8") as f:
                json.dump(json_result, f, indent=2)


# https://docs.python.org/3/library/zipfile.html#zipfile-objects
ZIP_TYPES_ACCEPTED = {
    "lzma": zipfile.ZIP_LZMA,
    "stored": zipfile.ZIP_STORED,
    "deflated": zipfile.ZIP_DEFLATED,
    "bzip2": zipfile.ZIP_BZIP2,
}


def output_to_zip(filename: str, error: Optional[str], results: Dict, zip_type: str = "lzma"):
    """
    Output the results to a zip
    The file in the zip is named slither_results.json
    Note: the json file will not have indentation, as a result the resulting json file will be smaller
    :param zip_type:
    :param filename:
    :param error:
    :param results:
    :return:
    """
    json_result = {"success": error is None, "error": error, "results": results}
    if os.path.isfile(filename):
        logger.info(yellow(f"{filename} exists already, the overwrite is prevented"))
    else:
        with ZipFile(
            filename,
            "w",
            compression=ZIP_TYPES_ACCEPTED.get(zip_type, zipfile.ZIP_LZMA),
        ) as file_desc:
            file_desc.writestr("slither_results.json", json.dumps(json_result).encode("utf8"))


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
        raise SlitherError(f"{d} does not inherit from SourceMapping, conversion impossible")

    if isinstance(d, Node):
        if d.expression:
            return f"{d.expression} ({d.source_mapping_str})"
        return f"{str(d)} ({d.source_mapping_str})"

    if hasattr(d, "canonical_name"):
        return f"{d.canonical_name} ({d.source_mapping_str})"

    if hasattr(d, "name"):
        return f"{d.name} ({d.source_mapping_str})"

    raise SlitherError(f"{type(d)} cannot be converted (no name, or canonical_name")


def _convert_to_markdown(d, markdown_root):
    if isinstance(d, str):
        return d

    if not isinstance(d, SourceMapping):
        raise SlitherError(f"{d} does not inherit from SourceMapping, conversion impossible")

    if isinstance(d, Node):
        if d.expression:
            return f"[{d.expression}]({d.source_mapping_to_markdown(markdown_root)})"
        return f"[{str(d)}]({d.source_mapping_to_markdown(markdown_root)})"

    if hasattr(d, "canonical_name"):
        return f"[{d.canonical_name}]({d.source_mapping_to_markdown(markdown_root)})"

    if hasattr(d, "name"):
        return f"[{d.name}]({d.source_mapping_to_markdown(markdown_root)})"

    raise SlitherError(f"{type(d)} cannot be converted (no name, or canonical_name")


def _convert_to_id(d):
    """
    Id keeps the source mapping of the node, otherwise we risk to consider two different node as the same
    :param d:
    :return:
    """
    if isinstance(d, str):
        return d

    if not isinstance(d, SourceMapping):
        raise SlitherError(f"{d} does not inherit from SourceMapping, conversion impossible")

    if isinstance(d, Node):
        if d.expression:
            return f"{d.expression} ({d.source_mapping_str})"
        return f"{str(d)} ({d.source_mapping_str})"

    if isinstance(d, Pragma):
        return f"{d} ({d.source_mapping_str})"

    if hasattr(d, "canonical_name"):
        return f"{d.canonical_name}"

    if hasattr(d, "name"):
        return f"{d.name}"

    raise SlitherError(f"{type(d)} cannot be converted (no name, or canonical_name")


# endregion
###################################################################################
###################################################################################
# region Internal functions
###################################################################################
###################################################################################


def _create_base_element(
    custom_type, name, source_mapping, type_specific_fields=None, additional_fields=None
):
    if additional_fields is None:
        additional_fields = {}
    if type_specific_fields is None:
        type_specific_fields = {}
    element = {"type": custom_type, "name": name, "source_mapping": source_mapping}
    if type_specific_fields:
        element["type_specific_fields"] = type_specific_fields
    if additional_fields:
        element["additional_fields"] = additional_fields
    return element


def _create_parent_element(element):
    # pylint: disable=import-outside-toplevel
    from slither.core.children.child_contract import ChildContract
    from slither.core.children.child_function import ChildFunction
    from slither.core.children.child_inheritance import ChildInheritance

    if isinstance(element, ChildInheritance):
        if element.contract_declarer:
            contract = Output("")
            contract.add_contract(element.contract_declarer)
            return contract.data["elements"][0]
    elif isinstance(element, ChildContract):
        if element.contract:
            contract = Output("")
            contract.add_contract(element.contract)
            return contract.data["elements"][0]
    elif isinstance(element, ChildFunction):
        if element.function:
            function = Output("")
            function.add_function(element.function)
            return function.data["elements"][0]
    return None


SupportedOutput = Union[Variable, Contract, Function, Enum, Event, Structure, Pragma, Node]


class Output:
    def __init__(
        self,
        info_: Union[str, List[Union[str, SupportedOutput]]],
        additional_fields: Optional[Dict] = None,
        markdown_root="",
        standard_format=True,
    ):
        if additional_fields is None:
            additional_fields = {}

        # Allow info to be a string to simplify the API
        info: List[Union[str, SupportedOutput]]
        if isinstance(info_, str):
            info = [info_]
        else:
            info = info_

        self._data: Dict[str, Any] = OrderedDict()
        self._data["elements"] = []
        self._data["description"] = "".join(_convert_to_description(d) for d in info)
        self._data["markdown"] = "".join(_convert_to_markdown(d, markdown_root) for d in info)
        self._data["first_markdown_element"] = ""
        self._markdown_root = markdown_root

        id_txt = "".join(_convert_to_id(d) for d in info)
        self._data["id"] = hashlib.sha3_256(id_txt.encode("utf-8")).hexdigest()

        if standard_format:
            to_add = [i for i in info if not isinstance(i, str)]

            for add in to_add:
                self.add(add)

        if additional_fields:
            self._data["additional_fields"] = additional_fields

    def add(self, add: SupportedOutput, additional_fields: Optional[Dict] = None):
        if not self._data["first_markdown_element"]:
            self._data["first_markdown_element"] = add.source_mapping_to_markdown(
                self._markdown_root
            )
        if isinstance(add, Variable):
            self.add_variable(add, additional_fields=additional_fields)
        elif isinstance(add, Contract):
            self.add_contract(add, additional_fields=additional_fields)
        elif isinstance(add, Function):
            self.add_function(add, additional_fields=additional_fields)
        elif isinstance(add, Enum):
            self.add_enum(add, additional_fields=additional_fields)
        elif isinstance(add, Event):
            self.add_event(add, additional_fields=additional_fields)
        elif isinstance(add, Structure):
            self.add_struct(add, additional_fields=additional_fields)
        elif isinstance(add, Pragma):
            self.add_pragma(add, additional_fields=additional_fields)
        elif isinstance(add, Node):
            self.add_node(add, additional_fields=additional_fields)
        else:
            raise SlitherError(f"Impossible to add {type(add)} to the json")

    @property
    def data(self) -> Dict:
        return self._data

    @property
    def elements(self) -> List[Dict]:
        return self._data["elements"]

    # endregion
    ###################################################################################
    ###################################################################################
    # region Variables
    ###################################################################################
    ###################################################################################

    def add_variable(self, variable: Variable, additional_fields: Optional[Dict] = None):
        if additional_fields is None:
            additional_fields = {}
        type_specific_fields = {"parent": _create_parent_element(variable)}
        element = _create_base_element(
            "variable",
            variable.name,
            variable.source_mapping,
            type_specific_fields,
            additional_fields,
        )
        self._data["elements"].append(element)

    def add_variables(self, variables: List[Variable]):
        for variable in sorted(variables, key=lambda x: x.name):
            self.add_variable(variable)

    # endregion
    ###################################################################################
    ###################################################################################
    # region Contract
    ###################################################################################
    ###################################################################################

    def add_contract(self, contract: Contract, additional_fields: Optional[Dict] = None):
        if additional_fields is None:
            additional_fields = {}
        element = _create_base_element(
            "contract", contract.name, contract.source_mapping, {}, additional_fields
        )
        self._data["elements"].append(element)

    # endregion
    ###################################################################################
    ###################################################################################
    # region Functions
    ###################################################################################
    ###################################################################################

    def add_function(self, function: Function, additional_fields: Optional[Dict] = None):
        if additional_fields is None:
            additional_fields = {}
        type_specific_fields = {
            "parent": _create_parent_element(function),
            "signature": function.full_name,
        }
        element = _create_base_element(
            "function",
            function.name,
            function.source_mapping,
            type_specific_fields,
            additional_fields,
        )
        self._data["elements"].append(element)

    def add_functions(self, functions: List[Function], additional_fields: Optional[Dict] = None):
        if additional_fields is None:
            additional_fields = {}
        for function in sorted(functions, key=lambda x: x.name):
            self.add_function(function, additional_fields)

    # endregion
    ###################################################################################
    ###################################################################################
    # region Enum
    ###################################################################################
    ###################################################################################

    def add_enum(self, enum: Enum, additional_fields: Optional[Dict] = None):
        if additional_fields is None:
            additional_fields = {}
        type_specific_fields = {"parent": _create_parent_element(enum)}
        element = _create_base_element(
            "enum",
            enum.name,
            enum.source_mapping,
            type_specific_fields,
            additional_fields,
        )
        self._data["elements"].append(element)

    # endregion
    ###################################################################################
    ###################################################################################
    # region Structures
    ###################################################################################
    ###################################################################################

    def add_struct(self, struct: Structure, additional_fields: Optional[Dict] = None):
        if additional_fields is None:
            additional_fields = {}
        type_specific_fields = {"parent": _create_parent_element(struct)}
        element = _create_base_element(
            "struct",
            struct.name,
            struct.source_mapping,
            type_specific_fields,
            additional_fields,
        )
        self._data["elements"].append(element)

    # endregion
    ###################################################################################
    ###################################################################################
    # region Events
    ###################################################################################
    ###################################################################################

    def add_event(self, event: Event, additional_fields: Optional[Dict] = None):
        if additional_fields is None:
            additional_fields = {}
        type_specific_fields = {
            "parent": _create_parent_element(event),
            "signature": event.full_name,
        }
        element = _create_base_element(
            "event",
            event.name,
            event.source_mapping,
            type_specific_fields,
            additional_fields,
        )

        self._data["elements"].append(element)

    # endregion
    ###################################################################################
    ###################################################################################
    # region Nodes
    ###################################################################################
    ###################################################################################

    def add_node(self, node: Node, additional_fields: Optional[Dict] = None):
        if additional_fields is None:
            additional_fields = {}
        type_specific_fields = {
            "parent": _create_parent_element(node),
        }
        node_name = str(node.expression) if node.expression else ""
        element = _create_base_element(
            "node",
            node_name,
            node.source_mapping,
            type_specific_fields,
            additional_fields,
        )
        self._data["elements"].append(element)

    def add_nodes(self, nodes: List[Node]):
        for node in sorted(nodes, key=lambda x: x.node_id):
            self.add_node(node)

    # endregion
    ###################################################################################
    ###################################################################################
    # region Pragma
    ###################################################################################
    ###################################################################################

    def add_pragma(self, pragma: Pragma, additional_fields: Optional[Dict] = None):
        if additional_fields is None:
            additional_fields = {}
        type_specific_fields = {"directive": pragma.directive}
        element = _create_base_element(
            "pragma",
            pragma.version,
            pragma.source_mapping,
            type_specific_fields,
            additional_fields,
        )
        self._data["elements"].append(element)

    # endregion
    ###################################################################################
    ###################################################################################
    # region File
    ###################################################################################
    ###################################################################################

    def add_file(self, filename: str, content: str, additional_fields: Optional[Dict] = None):
        if additional_fields is None:
            additional_fields = {}
        type_specific_fields = {"filename": filename, "content": content}
        element = _create_base_element("file", type_specific_fields, additional_fields)

        self._data["elements"].append(element)

    # endregion
    ###################################################################################
    ###################################################################################
    # region Pretty Table
    ###################################################################################
    ###################################################################################

    def add_pretty_table(
        self,
        content: MyPrettyTable,
        name: str,
        additional_fields: Optional[Dict] = None,
    ):
        if additional_fields is None:
            additional_fields = {}
        type_specific_fields = {"content": content.to_json(), "name": name}
        element = _create_base_element("pretty_table", type_specific_fields, additional_fields)

        self._data["elements"].append(element)

    # endregion
    ###################################################################################
    ###################################################################################
    # region Others
    ###################################################################################
    ###################################################################################

    def add_other(
        self,
        name: str,
        source_mapping,
        compilation_unit: "SlitherCompilationUnit",
        additional_fields: Optional[Dict] = None,
    ):
        # If this a tuple with (filename, start, end), convert it to a source mapping.
        if additional_fields is None:
            additional_fields = {}
        if isinstance(source_mapping, tuple):
            # Parse the source id
            (filename, start, end) = source_mapping
            source_id = next(
                (
                    source_unit_id
                    for (
                        source_unit_id,
                        source_unit_filename,
                    ) in compilation_unit.source_units.items()
                    if source_unit_filename == filename
                ),
                -1,
            )

            # Convert to a source mapping string
            source_mapping = f"{start}:{end}:{source_id}"

        # If this is a source mapping string, parse it.
        if isinstance(source_mapping, str):
            source_mapping_str = source_mapping
            source_mapping = SourceMapping()
            source_mapping.set_offset(source_mapping_str, compilation_unit)

        # If this is a source mapping object, get the underlying source mapping dictionary
        if isinstance(source_mapping, SourceMapping):
            source_mapping = source_mapping.source_mapping

        # Create the underlying element and add it to our resulting json
        element = _create_base_element("other", name, source_mapping, {}, additional_fields)
        self._data["elements"].append(element)
