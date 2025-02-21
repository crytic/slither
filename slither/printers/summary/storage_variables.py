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
            storage_vars = contract.storage_variables_ordered

            if not storage_vars:
                continue

            table = MyPrettyTable(
                ["Variable", "Type", "Visibility", "Slot", "Offset", "Inherited From"]
            )
            for field in table._field_names:
                table._options["set_alignment"] += [(field, "l")]

            contract_info = [
                f"\nContract {Colors.BOLD}{Colors.YELLOW}{contract.name}{Colors.END}"
                f" ({contract.source_mapping})"
            ]

            for v in storage_vars:
                slot, offset = contract.compilation_unit.storage_layout_of(contract, v)
                inherited = v.contract.name if v.contract != contract else ""
                table.add_row(
                    [
                        f"{Colors.BOLD}{Colors.RED}{v.name}{Colors.END}",
                        f"{Colors.GREEN}{v.type}{Colors.END}",
                        f"{Colors.BLUE}{v.visibility}{Colors.END}",
                        slot,
                        offset,
                        f"{Colors.MAGENTA}{inherited}{Colors.END}",
                    ]
                )

            all_contracts.append("\n".join(contract_info + [str(table)]))

        info = "\n".join(all_contracts) if all_contracts else ""
        self.info(info)
        return self.generate_output(info)
