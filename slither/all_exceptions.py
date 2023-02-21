"""
This module import all slither exceptions
"""
from slither.core.exceptions import SlitherCoreError
from slither.exceptions import SlitherException

# pylint: disable=unused-import
from slither.slithir.exceptions import SlithIRError
from slither.solc_parsing.exceptions import ParsingError, VariableNotFound
