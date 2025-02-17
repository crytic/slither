"""
Module printing all storage variables of the contracts
"""

from slither.printers.abstract_printer import AbstractPrinter
from slither.utils.colors import Colors
from slither.utils.output import Output
from slither.utils.myprettytable import MyPrettyTable


class PrinterStorageVariables(AbstractPrinter):

    ARGUMENT = "storage-variables"
    HELP = "Print all storage variables of the contracts"

    WIKI = "https://github.com/trailofbits/slither/wiki/Printer-documentation#storage-variables"

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
                if not c.is_test and not c.is_from_dependency()
            ),
            key=lambda x: x.name,
        ):
            storage_vars = [
                v for v in contract.state_variables if not (v.is_constant or v.is_immutable)
            ]

            if not storage_vars:
                continue

            table = MyPrettyTable(["Variable", "Type", "Visibility", "Slot", "Inherited From"])
            contract_info = [
                f"\nContract {Colors.BOLD}{Colors.YELLOW}{contract.name}{Colors.END}"
                f" ({contract.source_mapping})"
            ]

            storage_vars = sorted(
                storage_vars,
                key=lambda x, contract=contract: contract.compilation_unit.storage_layout_of(
                    contract, x
                )[0],
            )

            for v in storage_vars:
                slot = contract.compilation_unit.storage_layout_of(contract, v)[0]
                inherited = v.contract.name if v.contract != contract else ""
                table.add_row(
                    [
                        f"{Colors.BOLD}{Colors.RED}{v.name}{Colors.END}",
                        f"{Colors.GREEN}{str(v.type)}{Colors.END}",
                        f"{Colors.BLUE}{v.visibility}{Colors.END}",
                        str(slot),
                        f"{Colors.MAGENTA}{inherited}{Colors.END}" if inherited else "",
                    ]
                )

            all_contracts.append("\n".join(contract_info + [str(table)]))

        info = "\n".join(all_contracts) if all_contracts else ""
        self.info(info)
        return self.generate_output(info)
