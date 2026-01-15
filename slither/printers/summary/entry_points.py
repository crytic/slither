"""
Module printing all the state-changing entry point functions and their variables of the contracts
"""

from pathlib import Path
from slither.printers.abstract_printer import AbstractPrinter
from slither.core.declarations.function_contract import FunctionContract
from slither.utils.colors import Colors
from slither.utils.output import Output
from slither.utils.myprettytable import MyPrettyTable
from slither.utils.tests_pattern import is_test_file


class PrinterEntryPoints(AbstractPrinter):
    ARGUMENT = "entry-points"
    HELP = "Print all the state-changing entry point functions and their variables of the contracts"

    WIKI = "https://github.com/trailofbits/slither/wiki/Printer-documentation#entry-points"

    def output(self, _filename) -> Output:
        """
        _filename is not used
        Args:
            _filename(string)
        """
        all_contracts = []

        for contract in sorted(
            (
                c
                for c in self.slither.contracts_derived
                if not c.is_test
                and not c.is_from_dependency()
                and not is_test_file(Path(c.source_mapping.filename.absolute))
                and not c.is_interface
                and not c.is_library
                and not c.is_abstract
            ),
            key=lambda x: x.name,
        ):
            entry_points = [
                f
                for f in contract.functions
                if (
                    f.visibility in ["public", "external"]
                    and isinstance(f, FunctionContract)
                    and not f.view
                    and not f.pure
                    and not f.is_shadowed
                )
            ]

            if not entry_points:
                continue

            inheritance_chain = self._get_inheritance_chain(contract)
            inheritance_str = f" is {' is '.join(inheritance_chain)}" if inheritance_chain else ""

            contract_info = [
                f"\n\nContract {Colors.BOLD}{Colors.YELLOW}{contract.name}{Colors.END}{inheritance_str}"
                f" ({contract.source_mapping})"
            ]

            variables_info = self._get_variables_info(contract)
            if variables_info:
                var_table = MyPrettyTable(["Variables", "Types", "Inherited From"])
                for var_name, var_type, inherited_from in variables_info:
                    var_table.add_row(
                        [
                            f"{Colors.BOLD}{Colors.BLUE}{var_name}{Colors.END}",
                            f"{Colors.GREEN}{var_type}{Colors.END}",
                            (
                                f"{Colors.MAGENTA}{inherited_from}{Colors.END}"
                                if inherited_from
                                else ""
                            ),
                        ]
                    )
                contract_info.append(str(var_table))

            func_table = MyPrettyTable(["Functions", "Modifiers", "Inherited From"])

            self._add_function_rows(func_table, entry_points, contract)

            contract_info.append(str(func_table))
            all_contracts.append("\n".join(contract_info))

        info = "\n".join(all_contracts) if all_contracts else ""
        self.info(info)
        return self.generate_output(info)

    def _get_inheritance_chain(self, contract):
        """Get the full inheritance chain for a contract"""
        inheritance_chain = []
        for base in contract.inheritance:
            if not base.is_interface and not base.is_library:
                inheritance_chain.append(base.name)
        return inheritance_chain

    def _get_variables_info(self, contract):
        """Get all state variables with their types and inheritance info"""
        variables_info = []

        for variable in contract.storage_variables_ordered:
            var_type = str(variable.type)
            inherited_from = variable.contract.name if variable.contract != contract else ""
            variables_info.append((variable.name, var_type, inherited_from))

        return variables_info

    def _add_function_rows(self, func_table, entry_points, contract):
        """Add function rows to the functions table"""
        for f in sorted(
            entry_points,
            key=lambda x, contract=contract: (
                x.contract_declarer != contract,
                x.contract_declarer.name if x.contract_declarer != contract else "",
                x.source_mapping.start,
            ),
        ):
            name_parts = f.full_name.split("(", 1)
            inherited = f.contract_declarer.name if f.contract_declarer != contract else ""
            modifiers = ", ".join(
                [m.name for m in f.modifiers] + (["payable"] if f.payable else [])
            )

            if f.is_constructor or f.name in ["receive", "fallback"]:
                function_color = f"{Colors.BOLD}{Colors.MAGENTA}"
            else:
                function_color = f"{Colors.BOLD}{Colors.RED}"

            function_name = name_parts[0]

            func_table.add_row(
                [
                    f"{function_color}{function_name}{Colors.END}({name_parts[1]}",
                    f"{Colors.GREEN}{modifiers}{Colors.END}" if modifiers else "",
                    f"{Colors.MAGENTA}{inherited}{Colors.END}" if inherited else "",
                ]
            )
