"""
Module printing all the state-changing entry point functions of the contracts
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
    HELP = "Print all the state-changing entry point functions of the contracts"

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
                    and not f.is_constructor
                    and not f.view
                    and not f.pure
                    and not f.is_shadowed
                )
            ]

            if not entry_points:
                continue

            table = MyPrettyTable(["Function", "Modifiers", "Inherited From"])
            contract_info = [
                f"\nContract {Colors.BOLD}{Colors.YELLOW}{contract.name}{Colors.END}"
                f" ({contract.source_mapping})"
            ]

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

                table.add_row(
                    [
                        f"{Colors.BOLD}{Colors.RED}{name_parts[0]}{Colors.END}({name_parts[1]}",
                        f"{Colors.GREEN}{modifiers}{Colors.END}" if modifiers else "",
                        f"{Colors.MAGENTA}{inherited}{Colors.END}" if inherited else "",
                    ]
                )

            all_contracts.append("\n".join(contract_info + [str(table)]))

        info = "\n".join(all_contracts) if all_contracts else ""
        self.info(info)
        return self.generate_output(info)
