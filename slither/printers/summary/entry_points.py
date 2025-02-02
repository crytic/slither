"""
Module printing all the state-changing entry point functions of the contracts
"""

from slither.printers.abstract_printer import AbstractPrinter
from slither.core.declarations.function_contract import FunctionContract
from slither.utils.colors import Colors
from slither.utils.output import Output
from slither.utils.myprettytable import MyPrettyTable


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
                for c in self.contracts
                if not c.is_interface
                and not c.is_library
                and not c.is_abstract
                and "lib/" not in c.source_mapping.filename.absolute
                and "node_modules/" not in c.source_mapping.filename.absolute
                and not any(
                    mock in c.source_mapping.filename.absolute.lower() for mock in ["mock", "mocks"]
                )
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
                    and not f.is_fallback
                    and not f.is_receive
                    and not f.view
                    and not f.pure
                    and not f.contract_declarer.is_interface
                    and not f.contract_declarer.is_library
                    and not f.is_shadowed
                )
            ]

            if not entry_points:
                continue

            table = MyPrettyTable(["Function", "Modifiers", "Inherited From"])
            contract_info = [
                f"\nContract {Colors.BOLD}{Colors.YELLOW}{contract.name}{Colors.END}"
                f" ({contract.source_mapping.filename.relative})"
            ]

            for f in sorted(
                entry_points,
                key=lambda x: (x.visibility != "external", x.visibility != "public", x.full_name),
            ):
                modifiers = f"{', '.join(m.name for m in f.modifiers)}" if f.modifiers else ""
                inherited = f"{f.contract_declarer.name}" if f.contract_declarer != contract else ""
                function_name = (
                    f"{Colors.BOLD}{Colors.RED}{f.solidity_signature.split('(')[0]}{Colors.END}"
                )

                table.add_row(
                    [
                        function_name,
                        f"{Colors.GREEN}{modifiers}{Colors.END}" if modifiers else "",
                        f"{Colors.MAGENTA}{inherited}{Colors.END}" if inherited else "",
                    ]
                )

            contract_info.append(str(table))
            all_contracts.append("\n".join(contract_info))

        info = "\n".join(all_contracts) if all_contracts else ""
        self.info(info)
        return self.generate_output(info)
