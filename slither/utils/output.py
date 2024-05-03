from enum import Enum as PythonEnum
import hashlib
import json
import logging
import os
import zipfile
from collections import OrderedDict, defaultdict
from importlib import metadata
from pathlib import Path
from typing import Tuple, Optional, Dict, List, Union, Any, TYPE_CHECKING, Type
from zipfile import ZipFile

from crytic_compile.platform.standard import generate_standard_export

from slither.core.cfg.node import Node
from slither.core.declarations import (
    Contract,
    Function,
    Enum,
    Event,
    Structure,
    Pragma,
    FunctionContract,
    CustomError,
)
from slither.core.source_mapping.source_mapping import SourceMapping
from slither.core.variables.local_variable import LocalVariable
from slither.core.variables.variable import Variable
from slither.exceptions import SlitherError
from slither.utils.colors import yellow
from slither.utils.myprettytable import MyPrettyTable
from slither.utils.output_capture import StandardOutputCapture

if TYPE_CHECKING:
    from slither.core.compilation_unit import SlitherCompilationUnit
    from slither.printers.abstract_printer import AbstractPrinter
    from slither.detectors.abstract_detector import AbstractDetector

logger = logging.getLogger("Slither")

###################################################################################
###################################################################################
# region Output
###################################################################################
###################################################################################


def output_to_json(filename: Optional[str], error, results: Dict) -> None:
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


def _output_result_to_sarif(
    detector: Dict, detectors_classes: List["AbstractDetector"], sarif: Dict
) -> None:
    confidence = "very-high"
    if detector["confidence"] == "Medium":
        confidence = "high"
    elif detector["confidence"] == "Low":
        confidence = "medium"
    elif detector["confidence"] == "Informational":
        confidence = "low"

    risk = "0.0"
    if detector["impact"] == "High":
        risk = "8.0"
    elif detector["impact"] == "Medium":
        risk = "4.0"
    elif detector["impact"] == "Low":
        risk = "3.0"

    detector_class = next((d for d in detectors_classes if d.ARGUMENT == detector["check"]))
    check_id = (
        str(detector_class.IMPACT.value)
        + "-"
        + str(detector_class.CONFIDENCE.value)
        + "-"
        + detector["check"]
    )

    rule = {
        "id": check_id,
        "name": detector["check"],
        "properties": {"precision": confidence, "security-severity": risk},
        "shortDescription": {"text": detector_class.WIKI_TITLE},
        "help": {"text": detector_class.WIKI_RECOMMENDATION},
    }
    # Add the rule if does not exist yet
    if len([x for x in sarif["runs"][0]["tool"]["driver"]["rules"] if x["id"] == check_id]) == 0:
        sarif["runs"][0]["tool"]["driver"]["rules"].append(rule)

    if not detector["elements"]:
        logger.info(yellow("Cannot generate Github security alert for finding without location"))
        logger.info(yellow(detector["description"]))
        logger.info(yellow("This will be supported in a future Slither release"))
        return

    # From 3.19.10 (http://docs.oasis-open.org/sarif/sarif/v2.0/csprd01/sarif-v2.0-csprd01.html)
    # The locations array SHALL NOT contain more than one element unless the condition indicated by the result,
    # if any, can only be corrected by making a change at every location specified in the array.
    finding = detector["elements"][0]
    path = finding["source_mapping"]["filename_relative"]
    start_line = finding["source_mapping"]["lines"][0]
    end_line = finding["source_mapping"]["lines"][-1]

    sarif["runs"][0]["results"].append(
        {
            "ruleId": check_id,
            "message": {"text": detector["description"], "markdown": detector["markdown"]},
            "level": "warning",
            "locations": [
                {
                    "physicalLocation": {
                        "artifactLocation": {"uri": path},
                        "region": {"startLine": start_line, "endLine": end_line},
                    }
                }
            ],
            "partialFingerprints": {"id": detector["id"]},
        }
    )


def output_to_sarif(
    filename: Optional[str], results: Dict, detectors_classes: List[Type["AbstractDetector"]]
) -> None:
    """

    :param filename:
    :type filename:
    :param results:
    :type results:
    :return:
    :rtype:
    """

    sarif: Dict[str, Any] = {
        "$schema": "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json",
        "version": "2.1.0",
        "runs": [
            {
                "tool": {
                    "driver": {
                        "name": "Slither",
                        "informationUri": "https://github.com/crytic/slither",
                        "version": metadata.version("slither-analyzer"),
                        "rules": [],
                    }
                },
                "results": [],
            }
        ],
    }

    for detector in results.get("detectors", []):
        _output_result_to_sarif(detector, detectors_classes, sarif)

    if filename == "-":
        filename = None

    # Determine if we should output to stdout
    if filename is None:
        # Write json to console
        print(json.dumps(sarif))
    else:
        # Write json to file
        if os.path.isfile(filename):
            logger.info(yellow(f"{filename} exists already, the overwrite is prevented"))
        else:
            with open(filename, "w", encoding="utf8") as f:
                json.dump(sarif, f, indent=2)


class ZipType(str, PythonEnum):
    LZMA = "lzma"
    STORED = "stored"
    DEFLATED = "deflated"
    BZIP2 = "bzip2"

    @classmethod
    def get_zip_type(cls, value: "ZipType"):
        mapping = {
            cls.LZMA: zipfile.ZIP_LZMA,
            cls.STORED: zipfile.ZIP_STORED,
            cls.DEFLATED: zipfile.ZIP_DEFLATED,
            cls.BZIP2: zipfile.ZIP_BZIP2,
        }

        try:
            return mapping[value]
        except ValueError as exc:
            msg = f"Invalid zip type: {value}"
            raise ValueError(msg) from exc


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


def _convert_to_description(d: str) -> str:
    if isinstance(d, str):
        return d

    if not isinstance(d, SourceMapping):
        raise SlitherError(f"{d} does not inherit from SourceMapping, conversion impossible")

    if isinstance(d, Node):
        if d.expression:
            return f"{d.expression} ({d.source_mapping})"
        return f"{str(d)} ({d.source_mapping})"

    if hasattr(d, "canonical_name"):
        return f"{d.canonical_name} ({d.source_mapping})"

    if hasattr(d, "name"):
        return f"{d.name} ({d.source_mapping})"

    raise SlitherError(f"{type(d)} cannot be converted (no name, or canonical_name")


def _convert_to_markdown(d: str, markdown_root: str) -> str:
    if isinstance(d, str):
        return d

    if not isinstance(d, SourceMapping):
        raise SlitherError(f"{d} does not inherit from SourceMapping, conversion impossible")

    if isinstance(d, Node):
        if d.expression:
            return f"[{d.expression}]({d.source_mapping.to_markdown(markdown_root)})"
        return f"[{str(d)}]({d.source_mapping.to_markdown(markdown_root)})"

    if hasattr(d, "canonical_name"):
        return f"[{d.canonical_name}]({d.source_mapping.to_markdown(markdown_root)})"

    if hasattr(d, "name"):
        return f"[{d.name}]({d.source_mapping.to_markdown(markdown_root)})"

    raise SlitherError(f"{type(d)} cannot be converted (no name, or canonical_name")


def _convert_to_id(d: str) -> str:
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
            return f"{d.expression} ({d.source_mapping})"
        return f"{str(d)} ({d.source_mapping})"

    if isinstance(d, Pragma):
        return f"{d} ({d.source_mapping})"

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
    custom_type: str,
    name: str,
    source_mapping: Dict,
    type_specific_fields: Optional[
        Dict[
            str,
            Union[
                Dict[
                    str,
                    Union[
                        str,
                        Dict[str, Union[int, str, bool, List[int]]],
                        Dict[
                            str,
                            Union[
                                Dict[str, Union[str, Dict[str, Union[int, str, bool, List[int]]]]],
                                str,
                            ],
                        ],
                    ],
                ],
                Dict[str, Union[str, Dict[str, Union[int, str, bool, List[int]]]]],
                str,
                List[str],
            ],
        ]
    ] = None,
    additional_fields: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
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


def _create_parent_element(
    element: SourceMapping,
) -> Dict[
    str,
    Union[
        str,
        Dict[str, Union[int, str, bool, List[int]]],
        Dict[str, Union[Dict[str, Union[str, Dict[str, Union[int, str, bool, List[int]]]]], str]],
    ],
]:
    # pylint: disable=import-outside-toplevel
    from slither.core.declarations.contract_level import ContractLevel

    if isinstance(element, FunctionContract):
        if element.contract_declarer:
            contract = Output("")
            contract.add_contract(element.contract_declarer)
            return contract.data["elements"][0]
    elif isinstance(element, ContractLevel):
        if element.contract:
            contract = Output("")
            contract.add_contract(element.contract)
            return contract.data["elements"][0]
    elif isinstance(element, (LocalVariable, Node)):
        if element.function:
            function = Output("")
            function.add_function(element.function)
            return function.data["elements"][0]
    return None


SupportedOutput = Union[Variable, Contract, Function, Enum, Event, Structure, Pragma, Node]
AllSupportedOutput = Union[str, SupportedOutput]


class Output:
    def __init__(
        self,
        info_: Union[str, List[Union[str, SupportedOutput]]],
        additional_fields: Optional[Dict] = None,
        markdown_root: str = "",
        standard_format: bool = True,
    ) -> None:
        if additional_fields is None:
            additional_fields = {}

        # Allow info to be a string to simplify the API
        info: List[Union[str, SupportedOutput]]
        if isinstance(info_, str):
            info = [info_]
        else:
            info = info_

        self._data = OrderedDict()
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

    def add(self, add: SupportedOutput, additional_fields: Optional[Dict] = None) -> None:
        if not self._data["first_markdown_element"]:
            self._data["first_markdown_element"] = add.source_mapping.to_markdown(
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
        elif isinstance(add, CustomError):
            self.add_custom_error(add, additional_fields=additional_fields)
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

    def add_variable(self, variable: Variable, additional_fields: Optional[Dict] = None) -> None:
        if additional_fields is None:
            additional_fields = {}
        type_specific_fields = {"parent": _create_parent_element(variable)}
        element = _create_base_element(
            "variable",
            variable.name,
            variable.source_mapping.to_json(),
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

    def add_contract(self, contract: Contract, additional_fields: Optional[Dict] = None) -> None:
        if additional_fields is None:
            additional_fields = {}
        element = _create_base_element(
            "contract", contract.name, contract.source_mapping.to_json(), {}, additional_fields
        )
        self._data["elements"].append(element)

    # endregion
    ###################################################################################
    ###################################################################################
    # region Functions
    ###################################################################################
    ###################################################################################

    def add_function(self, function: Function, additional_fields: Optional[Dict] = None) -> None:
        if additional_fields is None:
            additional_fields = {}
        type_specific_fields = {
            "parent": _create_parent_element(function),
            "signature": function.full_name,
        }
        element = _create_base_element(
            "function",
            function.name,
            function.source_mapping.to_json(),
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

    def add_enum(self, enum: Enum, additional_fields: Optional[Dict] = None) -> None:
        if additional_fields is None:
            additional_fields = {}
        type_specific_fields = {"parent": _create_parent_element(enum)}
        element = _create_base_element(
            "enum",
            enum.name,
            enum.source_mapping.to_json(),
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

    def add_struct(self, struct: Structure, additional_fields: Optional[Dict] = None) -> None:
        if additional_fields is None:
            additional_fields = {}
        type_specific_fields = {"parent": _create_parent_element(struct)}
        element = _create_base_element(
            "struct",
            struct.name,
            struct.source_mapping.to_json(),
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

    def add_event(self, event: Event, additional_fields: Optional[Dict] = None) -> None:
        if additional_fields is None:
            additional_fields = {}
        type_specific_fields = {
            "parent": _create_parent_element(event),
            "signature": event.full_name,
        }
        element = _create_base_element(
            "event",
            event.name,
            event.source_mapping.to_json(),
            type_specific_fields,
            additional_fields,
        )

        self._data["elements"].append(element)

    # endregion
    ###################################################################################
    ###################################################################################
    # region CustomError
    ###################################################################################
    ###################################################################################

    def add_custom_error(
        self, custom_error: CustomError, additional_fields: Optional[Dict] = None
    ) -> None:
        if additional_fields is None:
            additional_fields = {}
        type_specific_fields = {
            "parent": _create_parent_element(custom_error),
            "signature": custom_error.full_name,
        }
        element = _create_base_element(
            "custom_error",
            custom_error.name,
            custom_error.source_mapping.to_json(),
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

    def add_node(self, node: Node, additional_fields: Optional[Dict] = None) -> None:
        if additional_fields is None:
            additional_fields = {}
        type_specific_fields = {
            "parent": _create_parent_element(node),
        }
        node_name = str(node.expression) if node.expression else ""
        element = _create_base_element(
            "node",
            node_name,
            node.source_mapping.to_json(),
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

    def add_pragma(self, pragma: Pragma, additional_fields: Optional[Dict] = None) -> None:
        if additional_fields is None:
            additional_fields = {}
        type_specific_fields = {"directive": pragma.directive}
        element = _create_base_element(
            "pragma",
            pragma.version,
            pragma.source_mapping.to_json(),
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
        source_mapping: Tuple[str, int, int],
        compilation_unit: "SlitherCompilationUnit",
        additional_fields: Optional[Dict] = None,
    ) -> None:
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
            source_mapping = source_mapping.source_mapping.to_json()

        # Create the underlying element and add it to our resulting json
        element = _create_base_element("other", name, source_mapping, {}, additional_fields)
        self._data["elements"].append(element)


def output_results_to_markdown(
    all_results: List[Dict], checklistlimit: int, show_ignored_findings: bool
) -> None:
    checks = defaultdict(list)
    info: Dict = defaultdict(dict)
    for results_ in all_results:
        checks[results_["check"]].append(results_)
        info[results_["check"]] = {
            "impact": results_["impact"],
            "confidence": results_["confidence"],
        }

    if not show_ignored_findings:
        print(
            "**THIS CHECKLIST IS NOT COMPLETE**. Use `--show-ignored-findings` to show all the results."
        )

    print("Summary")
    for check_ in checks:
        print(
            f" - [{check_}](#{check_}) ({len(checks[check_])} results) ({info[check_]['impact']})"
        )

    counter = 0
    for (check, results) in checks.items():
        print(f"## {check}")
        print(f'Impact: {info[check]["impact"]}')
        print(f'Confidence: {info[check]["confidence"]}')
        additional = False
        if checklistlimit and len(results) > 5:
            results = results[0:5]
            additional = True
        for result in results:
            print(" - [ ] ID-" + f"{counter}")
            counter = counter + 1
            print(result["markdown"])
            if result["first_markdown_element"]:
                print(result["first_markdown_element"])
                print("\n")
        if additional:
            print(f"**More results were found, check [{checklistlimit}]({checklistlimit})**")


class OutputFormat(str, PythonEnum):
    TEXT = "text"
    JSON = "json"
    SARIF = "sarif"
    ZIP = "zip"


# pylint: disable=too-many-arguments,too-many-locals
def format_output(
    output_format: OutputFormat,
    output_file: Path,
    slither_instances,
    results_detectors,
    results_printers,
    output_error,
    runned_detectors: Union[List[Type["AbstractDetector"]], None] = None,
    json_types: Union[None, List[str]] = None,
    zip_type: ZipType = ZipType.LZMA,
    checklist: bool = False,
    checklist_limit: int = 1,
    show_ignored_findings: bool = False,
    all_detectors: Union[None, List[Type["AbstractDetector"]]] = None,
    all_printers: Union[None, List[Type["AbstractPrinter"]]] = None,
):
    if output_format in (OutputFormat.JSON, OutputFormat.SARIF, OutputFormat.ZIP):
        json_results: Dict[str, Any] = {}

        if "compilation" in json_types:
            compilation_results = []
            for slither_instance in slither_instances:
                assert slither_instance.crytic_compile
                compilation_results.append(
                    generate_standard_export(slither_instance.crytic_compile)
                )
            json_results["compilations"] = compilation_results

        # Add our detector results to JSON if desired.
        if results_detectors and "detectors" in json_types:
            json_results["detectors"] = results_detectors

        # Add our printer results to JSON if desired.
        if results_printers and "printers" in json_types:
            json_results["printers"] = results_printers

        # Add our detector types to JSON
        if "list-detectors" in json_types:
            json_results["list-detectors"] = output_detectors_json(all_detectors)

        # Add our detector types to JSON
        if "list-printers" in json_types:
            json_results["list-printers"] = output_printers_json(all_printers)

        if output_format == OutputFormat.JSON:
            if "console" in json_types:
                json_results["console"] = {
                    "stdout": StandardOutputCapture.get_stdout_output(),
                    "stderr": StandardOutputCapture.get_stderr_output(),
                }
            StandardOutputCapture.disable()
            output_to_json(output_file.as_posix(), output_error, json_results)
        elif output_format == OutputFormat.SARIF:
            StandardOutputCapture.disable()
            output_to_sarif(output_file.as_posix(), json_results, runned_detectors)
        elif output_format == OutputFormat.ZIP:
            output_to_zip(output_file.as_posix(), output_error, json_results, zip_type.value)

    elif checklist is True:
        output_results_to_markdown(
            results_detectors,
            checklist_limit,
            show_ignored_findings,
        )


def output_to_markdown(
    detector_classes: List[Type["AbstractDetector"]],
    printer_classes: List[Type["AbstractPrinter"]],
    filter_wiki: str,
) -> None:
    def extract_help(cls: Union[Type["AbstractDetector"], Type["AbstractPrinter"]]) -> str:
        if cls.WIKI == "":
            return cls.HELP
        return f"[{cls.HELP}]({cls.WIKI})"

    detectors_list = []
    print(filter_wiki)
    for detector in detector_classes:
        argument = detector.ARGUMENT
        # dont show the backdoor example
        if argument == "backdoor":
            continue
        if not filter_wiki in detector.WIKI:
            continue
        help_info = extract_help(detector)
        impact = detector.IMPACT
        confidence = classification_txt[detector.CONFIDENCE]
        detectors_list.append((argument, help_info, impact, confidence))

    # Sort by impact, confidence, and name
    detectors_list = sorted(
        detectors_list, key=lambda element: (element[2], element[3], element[0])
    )
    idx = 1
    for (argument, help_info, impact, confidence) in detectors_list:
        print(f"{idx} | `{argument}` | {help_info} | {classification_txt[impact]} | {confidence}")
        idx = idx + 1

    print()
    printers_list = []
    for printer in printer_classes:
        argument = printer.ARGUMENT
        help_info = extract_help(printer)
        printers_list.append((argument, help_info))

    # Sort by impact, confidence, and name
    printers_list = sorted(printers_list, key=lambda element: (element[0]))
    idx = 1
    for (argument, help_info) in printers_list:
        print(f"{idx} | `{argument}` | {help_info}")
        idx = idx + 1


def convert_result_to_markdown(txt: str) -> str:
    def get_level(l: str) -> int:
        tab = l.count("\t") + 1
        if l.replace("\t", "").startswith(" -"):
            tab = tab + 1
        if l.replace("\t", "").startswith("-"):
            tab = tab + 1
        return tab

    # -1 to remove the last \n
    lines = txt[0:-1].split("\n")
    ret = []
    level = 0
    for l in lines:
        next_level = get_level(l)
        prefix = "<li>"
        if next_level < level:
            prefix = "</ul>" * (level - next_level) + prefix
        if next_level > level:
            prefix = "<ul>" * (next_level - level) + prefix
        level = next_level
        ret.append(prefix + l)

    return "".join(ret)


def output_wiki(detector_classes: List[Type["AbstractDetector"]], filter_wiki: str) -> None:

    # Sort by impact, confidence, and name
    detectors_list = sorted(
        detector_classes,
        key=lambda element: (element.IMPACT, element.CONFIDENCE, element.ARGUMENT),
    )

    for detector in detectors_list:
        argument = detector.ARGUMENT
        # dont show the backdoor example
        if argument == "backdoor":
            continue
        if not filter_wiki in detector.WIKI:
            continue
        check = detector.ARGUMENT
        impact = classification_txt[detector.IMPACT]
        confidence = classification_txt[detector.CONFIDENCE]
        title = detector.WIKI_TITLE
        description = detector.WIKI_DESCRIPTION
        exploit_scenario = detector.WIKI_EXPLOIT_SCENARIO
        recommendation = detector.WIKI_RECOMMENDATION

        print(f"\n## {title}")
        print("### Configuration")
        print(f"* Check: `{check}`")
        print(f"* Severity: `{impact}`")
        print(f"* Confidence: `{confidence}`")
        print("\n### Description")
        print(description)
        if exploit_scenario:
            print("\n### Exploit Scenario:")
            print(exploit_scenario)
        print("\n### Recommendation")
        print(recommendation)


def output_detectors(detector_classes: List[Type["AbstractDetector"]]) -> None:
    detectors_list = []
    for detector in detector_classes:
        argument = detector.ARGUMENT
        # dont show the backdoor example
        if argument == "backdoor":
            continue
        help_info = detector.HELP
        impact = detector.IMPACT
        confidence = classification_txt[detector.CONFIDENCE]
        detectors_list.append((argument, help_info, impact, confidence))
    table = MyPrettyTable(["Num", "Check", "What it Detects", "Impact", "Confidence"])

    # Sort by impact, confidence, and name
    detectors_list = sorted(
        detectors_list, key=lambda element: (element[2], element[3], element[0])
    )
    idx = 1
    for (argument, help_info, impact, confidence) in detectors_list:
        table.add_row([str(idx), argument, help_info, classification_txt[impact], confidence])
        idx = idx + 1
    print(table)


def output_detectors_json(
    detector_classes: List[Type["AbstractDetector"]],
) -> List[Dict]:
    detectors_list = []
    for detector in detector_classes:
        argument = detector.ARGUMENT
        # dont show the backdoor example
        if argument == "backdoor":
            continue
        help_info = detector.HELP
        impact = detector.IMPACT
        confidence = classification_txt[detector.CONFIDENCE]
        wiki_url = detector.WIKI
        wiki_description = detector.WIKI_DESCRIPTION
        wiki_exploit_scenario = detector.WIKI_EXPLOIT_SCENARIO
        wiki_recommendation = detector.WIKI_RECOMMENDATION
        detectors_list.append(
            (
                argument,
                help_info,
                impact,
                confidence,
                wiki_url,
                wiki_description,
                wiki_exploit_scenario,
                wiki_recommendation,
            )
        )

    # Sort by impact, confidence, and name
    detectors_list = sorted(
        detectors_list, key=lambda element: (element[2], element[3], element[0])
    )
    idx = 1
    table = []
    for (
        argument,
        help_info,
        impact,
        confidence,
        wiki_url,
        description,
        exploit,
        recommendation,
    ) in detectors_list:
        table.append(
            {
                "index": idx,
                "check": argument,
                "title": help_info,
                "impact": classification_txt[impact],
                "confidence": confidence,
                "wiki_url": wiki_url,
                "description": description,
                "exploit_scenario": exploit,
                "recommendation": recommendation,
            }
        )
        idx = idx + 1
    return table


def output_printers(printer_classes: List[Type["AbstractPrinter"]]) -> None:
    printers_list = []
    for printer in printer_classes:
        argument = printer.ARGUMENT
        help_info = printer.HELP
        printers_list.append((argument, help_info))
    table = MyPrettyTable(["Num", "Printer", "What it Does"])

    # Sort by impact, confidence, and name
    printers_list = sorted(printers_list, key=lambda element: (element[0]))
    idx = 1
    for (argument, help_info) in printers_list:
        table.add_row([str(idx), argument, help_info])
        idx = idx + 1
    print(table)


def output_printers_json(printer_classes: List[Type["AbstractPrinter"]]) -> List[Dict]:
    printers_list = []
    for printer in printer_classes:
        argument = printer.ARGUMENT
        help_info = printer.HELP

        printers_list.append((argument, help_info))

    # Sort by name
    printers_list = sorted(printers_list, key=lambda element: (element[0]))
    idx = 1
    table = []
    for (argument, help_info) in printers_list:
        table.append({"index": idx, "check": argument, "title": help_info})
        idx = idx + 1
    return table
