import logging
import re

from slither.slither import Slither
from slither.formatters.utils.patches import create_patch, apply_patch, create_diff
from slither.core.cfg.node import Node
from slither.core.declarations.function import Function
from slither.core.declarations.contract import Contract

logger = logging.getLogger("Slither-Log")

# pylint: disable=too-few-public-methods
class SolFile:
    def __init__(self, contract: Contract):
        self.contract = contract
        self.filename = contract.source_mapping.filename.absolute
        self.old_str = contract.compilation_unit.core.source_code[self.filename]
        self.new_str = self.old_str[:]
        self.margin = 0


# pylint: disable=too-few-public-methods,too-many-instance-attributes,dangerous-default-value
class SlitherLog:
    # pylint: disable=too-many-arguments
    def __init__(
        self,
        slither: Slither,
        convert_bytes: bool = False,
        whitelisted_functions: list[str] = [],
        blacklisted_functions: list[str] = [],
        whitelisted_contracts: list[str] = [],
        blacklisted_contracts: list[str] = [],
    ):
        self.slither = slither
        self.convert_bytes = convert_bytes
        self.whitelisted_functions = set(whitelisted_functions)
        self.blacklisted_functions = set(blacklisted_functions)
        self.whitelisted_contracts = set(whitelisted_contracts)
        self.blacklisted_contracts = set(blacklisted_contracts)
        self.acceptable_types = set(["uint", "addr", "stri", "bool", "byte"])
        self.diffs = ""

    @staticmethod
    def _convert_pure_to_view(function: Function, file: SolFile) -> None:
        """Converts pure functions to view to allow for console.log"""
        if function.pure:
            params_end = function.parameters_src().source_mapping.end
            returns_start = function.returns_src().source_mapping.start
            search_area = file.old_str[params_end:returns_start]
            regex = re.search(r"((\spure)\s+)|(\spure)$|(\)pure)$", search_area)
            index = params_end + regex.span()[0] + 1
            file.new_str = file.new_str[:index] + "view" + file.new_str[index + len("pure") :]

    def _set_file_margin(self, file: SolFile) -> None:
        """Sets left margin for a file (which varies based on presence/absence of '\r')"""
        for func in file.contract.functions:
            function = func
            if not self._is_bad_function(function, file.contract):
                break
        if self._is_bad_function(function, file.contract):
            return  # Contract is an interface
        start = function.entry_point.source_mapping.start
        while True:
            char = file.old_str[start + file.margin]
            if char not in set(["{", "\r", "\n", " "]):
                break
            file.margin += 1

    @staticmethod
    def _is_bad_function(function: Function, contract: Contract) -> bool:
        """Filters out invalid functions"""
        bad_function_names = set(
            ["constructor", "slitherConstructorVariables", "slitherConstructorConstantVariables"]
        )
        return (
            function.name in bad_function_names
            or function.canonical_name[: len(function.contract.name)]
            != contract.name  # function belongs to an imported contract
            or function.contract_declarer.contract_kind
            == "interface"  # interface functions have no implementation or entry_point so are invalid
            or function.entry_point.source_mapping.length
            == 2  # virtual functions with no implementation - "{}" - are invalid
        )

    def _generate_function_list(self, contract: Contract) -> list[Function]:
        """Generates a list of valid functions within a contract"""
        if contract.name in self.blacklisted_contracts:
            return []
        if self.whitelisted_contracts and contract.name not in self.whitelisted_contracts:
            return []

        functions = []
        for function in contract.functions_and_modifiers:
            if self._is_bad_function(function, contract):
                continue
            if function.canonical_name in self.blacklisted_functions:
                continue
            if (
                self.whitelisted_functions
                and function.canonical_name not in self.whitelisted_functions
            ):
                continue
            start = function.entry_point.source_mapping.start

            functions.append((start, function))
        # reverse sort so no offset is needed for insertions into source code string
        functions.sort(reverse=True)
        return functions

    # pylint: disable=bare-except
    def _convert_params(self, function: Function) -> list[str]:
        """Sorts params based on type and converts invalid types to be console.log compatible"""
        converted_params = []
        for param in function.parameters:
            try:
                param_type = param.type.name[:4]
            except:  # param is an array
                param_type = "invalid_type"

            if param_type in self.acceptable_types:
                if param_type == "byte":
                    if (
                        len(param.type.name)
                        == 5  # unspecified size 'bytes' is not valid - cant convert to uint256
                        or not self.convert_bytes
                    ):
                        converted_params.append("'unlogged_bytes'")
                    else:
                        converted_params.append(f"uint256(bytes32({param.name}))")
                else:
                    converted_params.append(param.name)
            else:
                converted_params.append("'unloggable_type'")

        return converted_params

    def _generate_entry_point_string(self, function: Function, file_margin: int) -> str:
        """Generates console.log line of code to be inserted at function entry point"""
        if function.parameters:
            params_string = (
                ", (" + ", ".join([f"{param.name} = %s" for param in function.parameters]) + ")"
            )
            # handle invalid types for console.log
            converted_params = self._convert_params(function)

            if len(function.parameters) < 4:  # console.log only handles string + 3 params
                params_values = ", " + ", ".join(converted_params)
                overflow_values = ""
            else:
                params_values = ", " + ", ".join(converted_params[:3])
                overflow_values = (
                    "\n"
                    + (file_margin - 2) * " "
                    + ("\n" + (file_margin - 2) * " ").join(
                        [f"console.log({param});" for param in converted_params[3:]]
                    )
                )
        else:
            params_string = params_values = overflow_values = ""

        return f"console.log('Enter {function.canonical_name}{params_string}'{params_values});{overflow_values}"

    # pylint: disable=too-many-arguments,too-many-locals
    def _generate_return_string(
        self, node: Node, num_nodes: int, function: Function, source_code: str, file_margin: int
    ) -> str:
        """Genarates console.log line of code to be inserted at a given return statement."""
        temp_start = node.expression.source_mapping.start
        temp_end = node.expression.source_mapping.end
        expression = source_code[temp_start:temp_end]

        # get rid of \n and \r since the string in solidity's console.log can't be several lines
        expression = expression.replace("\n", "").replace("\r", "")

        # handle tuples - console.log can't print tuple types
        if expression[0] == "(" and expression[-1] == ")":
            expression = expression[1:-1]
        return_expression = f"({expression})"

        return_types = self._get_return_types(function)
        if len(return_types) > 1 and num_nodes != len(return_types):
            sub_expressions = self._parse_return_expression(expression)
        else:
            sub_expressions = [expression]

        return_values = []

        for i, exp in enumerate(sub_expressions):
            if return_types[i] in self.acceptable_types:
                if "byte" == return_types[i]:
                    if len(function.return_type[0].name) == 5 or not self.convert_bytes:
                        return_values.append("'unlogged_bytes'")
                    else:
                        return_values.append(f"uint256(bytes32({exp}))")
                else:
                    return_values.append(exp)
            else:
                return_values.append("'unloggable_type'")

        values_string = ", ".join(return_values[:3])
        if len(return_values) > 3:
            overflow_string = (
                (file_margin - 2) * " "
                + ("\n" + (file_margin - 2) * " ").join(
                    [f"console.log({value});" for value in return_values[3:]]
                )
                + "\r"
            )
        else:
            overflow_string = ""

        return f"console.log('Return from {function.canonical_name}, returns {return_expression} =',{values_string});\n{overflow_string}"

    @staticmethod
    def _get_return_nodes(function: Function) -> list[Node]:
        """Return a list of return statements in a function"""
        return_nodes = []
        for node in function.nodes:
            if node.type.name == "RETURN":
                temp_start = node.source_mapping.start
                return_nodes.append((temp_start, node))

        return_nodes.sort(reverse=True, key=lambda a: a[0])

        return return_nodes

    @staticmethod
    def _parse_return_expression(expression: str) -> list[str]:
        """Splits expression into individual returns if more than 1 return value"""
        sub_expressions = []
        num_open_parentheses = 0
        num_open_brackets = 0
        left_pointer = right_pointer = 0
        while right_pointer < len(expression) - 1:
            if expression[right_pointer] == "(":
                num_open_parentheses += 1
            if expression[right_pointer] == "[":
                num_open_brackets += 1
            if expression[right_pointer] == ")":
                num_open_parentheses -= 1
            if expression[right_pointer] == "]":
                num_open_brackets -= 1
            if (
                expression[right_pointer] == ","
                and num_open_parentheses == 0
                and num_open_brackets == 0
            ):
                sub_expressions.append(expression[left_pointer:right_pointer])
                right_pointer += 1
                left_pointer = right_pointer
            right_pointer += 1
        sub_expressions.append(expression[left_pointer:])
        return sub_expressions

    # pylint: disable=pointless-statement
    @staticmethod
    def _get_return_types(function: Function) -> list[str]:
        """Returns a list of return types, separating out arrays"""
        return_types = []
        for item in function.return_type:
            try:
                item.type.type  # will throw error if not an array type
                return_types.append("array")
            # pylint: disable=bare-except
            except:
                try:
                    return_types.append(item.type[:4])
                except:
                    return_types.append("unloggable_type")

        return return_types

    def _generate_diffs(self, file: SolFile) -> None:
        """Uses original and edited source codes to create a diff string for the current contract"""
        result = {}
        start = 0
        stop = len(self.slither.source_code[file.filename])

        create_patch(
            result,
            file.filename,
            start,
            stop,
            file.old_str,
            file.new_str,
        )

        for res in result["patches"]:
            original_txt = file.old_str.encode("utf8")
            patched_txt = original_txt
            offset = 0
            patches = result["patches"][res]
            patches.sort(key=lambda x: x["start"])
            if not all(patches[i]["end"] <= patches[i + 1]["end"] for i in range(len(patches) - 1)):
                logger.info(f"Impossible to generate patch; patches collisions: {patches}")
                continue
            for patch in patches:
                patched_txt, offset = apply_patch(patched_txt, patch, offset)
            diff = create_diff(self.slither, original_txt, patched_txt, res)
            if not diff:
                logger.info(f"Impossible to generate patch; empty {patches}")
            self.diffs += diff

    def add_console_log(self) -> None:
        """Main function
        Adds console logs to function entry points and returns, then builds a diff
        for the target contract and all dependencies to be written to a git patch file
        """
        seen_files = set()
        for contract in self.slither.contracts:
            current_file = SolFile(contract)
            self._set_file_margin(current_file)

            functions = self._generate_function_list(contract)

            for start, function in functions:
                self._convert_pure_to_view(function, current_file)
                if function.returns:
                    return_nodes = self._get_return_nodes(function)
                    for (_, node) in return_nodes:
                        return_string = self._generate_return_string(
                            node,
                            len(return_nodes),
                            function,
                            current_file.old_str,
                            current_file.margin,
                        )
                        return_keyword_start_index = node.source_mapping.start

                        current_file.new_str = (
                            current_file.new_str[:return_keyword_start_index]
                            + return_string
                            + (current_file.margin - 2) * " "
                            + current_file.new_str[return_keyword_start_index:]
                        )
                entry_point_string = self._generate_entry_point_string(
                    function, current_file.margin
                )

                current_file.new_str = (
                    current_file.new_str[: start + current_file.margin]
                    + entry_point_string
                    + current_file.new_str[start + 1 :]
                )

            if current_file.filename not in seen_files:
                # add import hardhat console to top of file
                current_file.new_str = "import 'hardhat/console.sol';\n\n" + current_file.new_str
                seen_files.add(current_file.filename)

            # generate output
            self._generate_diffs(current_file)
