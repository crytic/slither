"""
Module printing all the state-changing entry point functions of the contracts
"""

from slither.printers.abstract_printer import AbstractPrinter
from slither.core.declarations.function_contract import FunctionContract
from slither.core.declarations.contract import Contract
from slither.utils.colors import Colors
from slither.utils.output import Output


class PrinterEntryPoints(AbstractPrinter):

    ARGUMENT = "entry-points"
    HELP = "Print all the state-changing entry point functions of the contracts"

    WIKI = "https://github.com/trailofbits/slither/wiki/Printer-documentation#entry-points"

    def _get_entry_points(self, contract: Contract) -> list:
        """
        Get filtered entry point functions for a contract.

        Filters out:
        - Non-public/external functions
        - Constructors
        - Fallback functions
        - Receive functions
        - View/Pure functions
        - Interface/Library functions

        Args:
            contract (Contract): The contract to analyze

        Returns:
            list: List of functions that are state-changing entry points
        """
        return [
            f
            for f in contract.functions
            if (
                f.visibility in ["public", "external"]
                and isinstance(f, FunctionContract)
                and not f.is_constructor
                and not f.is_fallback
                and not f.is_receive
                and not f.view
                and not f.pure
                and not f.contract_declarer.is_interface
                and not f.contract_declarer.is_library
            )
        ]

    def _format_function_info(self, function: FunctionContract, contract: Contract) -> str:
        """
        Format function information including modifiers and inheritance details.

        Args:
            function (FunctionContract): The function to format
            contract (Contract): The contract containing the function

        Returns:
            str: Formatted string containing function name, modifiers, and inheritance info
        """
        # Get list of modifier names if any exist
        modifiers = [m.name for m in function.modifiers] if function.modifiers else []
        modifier_str = f" [{', '.join(modifiers)}]" if modifiers else ""

        # Add inheritance information if function is inherited
        inherited_str = ""
        if function.contract_declarer != contract:
            inherited_str = f" (from {function.contract_declarer.name})"
        return f"        - {Colors.BOLD}{Colors.RED}{function.name}{Colors.END}{modifier_str}{inherited_str}"

    def output(self, filename: str) -> Output:
        """
        Generates a formatted output of all contract entry point functions.

        The output is organized by contract and includes:
        - Contract type (Abstract/Regular)
        - Contract name and source file
        - Inheritance information
        - List of entry point functions with their modifiers and inheritance details

        Contracts are filtered to exclude:
        - Interfaces and libraries
        - Contracts from library directories
        - Contracts from node_modules
        - Mock contracts

        Args:
            filename (str): The output filename (unused but required by interface)

        Returns:
            Output: Formatted output containing all entry point functions information
        """
        all_contracts = []

        # Filter out interfaces, libraries, and contracts from common dependency paths
        filtered_contracts = [
            c
            for c in self.contracts
            if not c.is_interface
            and not c.is_library
            and "lib/" not in c.source_mapping.filename.absolute
            and "node_modules/" not in c.source_mapping.filename.absolute
            and not any(
                mock in c.source_mapping.filename.absolute.lower() for mock in ["mock", "mocks"]
            )
        ]

        # Sort contracts: non-abstract first, then by name
        sorted_contracts = sorted(
            filtered_contracts,
            key=lambda x: (
                not x.is_abstract,
                x.name,
            ),
        )

        for contract in sorted_contracts:
            entry_points = self._get_entry_points(contract)
            if not entry_points:
                continue

            contract_info = []
            # Determine contract type and format source information
            contract_type = "Abstract Contract" if contract.is_abstract else "Contract"
            source_file = contract.source_mapping.filename.short

            # Add contract header with type, name, and source file
            contract_info.append(
                f"\n{contract_type} {Colors.BOLD}{Colors.BLUE}{contract.name}{Colors.END} ({source_file})"
            )

            # Add inheritance information if present
            if contract.inheritance:
                inheritance_str = ", ".join(c.name for c in contract.inheritance)
                contract_info.append(f"Inherits from: {inheritance_str}")

            # Sort entry point functions by visibility and name
            entry_points.sort(
                key=lambda x: (x.visibility != "external", x.visibility != "public", x.full_name)
            )

            # Add formatted function information for each entry point
            for f in entry_points:
                contract_info.append(self._format_function_info(f, contract))

            all_contracts.append("\n".join(contract_info))

        # Combine all contract information or return empty string if no contracts found
        info = "\n".join(all_contracts) if all_contracts else ""
        self.info(info)

        return self.generate_output(info)
