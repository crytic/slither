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
    from slither.detectors.abstract_detector import AbstractDetector

from slither.utils.output import (
    Output,
    SupportedOutput,
    _convert_to_id,
    _convert_to_markdown,
    _convert_to_description
)

logger = logging.getLogger("Slither")


class ProxyOutput(Output):
    """
    Custom Output subclass used by the proxy-patterns detector.
    Contains the minimum subset of keys that are present in the Output class
    which are required in order to make use of Slither's --json CLI option.
    i.e., the 'elements', 'description' and 'id' fields are necessary in
    order to pass the `valid_result` checks in slither/core/slither_core.py,
    though we don't need to populate the 'elements' field with source mapping
    information, which makes the json results output difficult to read.
    """
    def __init__(self,
                 contract: Optional[Contract],
                 info_: Union[str, List[Union[str, SupportedOutput]]],
                 additional_fields: Optional[Dict] = None,
                 markdown_root="",
                 standard_format=False
    ):
        super().__init__("", None, markdown_root, standard_format)
        if additional_fields is None:
            additional_fields = {}

        # Allow info to be a string to simplify the API
        info: List[Union[str, SupportedOutput]]
        if isinstance(info_, str):
            info = [info_]
        else:
            info = info_

        self._data: Dict[str, Any] = OrderedDict()
        if contract is not None:
            self._data["contract"] = _convert_to_description(contract)
        self._data["elements"] = []
        self._data["description"] = "".join(_convert_to_description(d) for d in info)
        # self._data["markdown"] = "".join(_convert_to_markdown(d, markdown_root) for d in info)
        # self._data["first_markdown_element"] = ""
        # self._markdown_root = markdown_root

        id_txt = "".join(_convert_to_id(d) for d in info)
        self._data["id"] = hashlib.sha3_256(id_txt.encode("utf-8")).hexdigest()

        # if standard_format:
        #     to_add = [i for i in info if not isinstance(i, str)]
        #
        #     for add in to_add:
        #         self.add(add)

        if additional_fields:
            self._data["features"] = additional_fields
