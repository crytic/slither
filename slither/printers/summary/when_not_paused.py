"""
    Module printing summary of the contract
"""

from typing import List, Set
from slither.printers.abstract_printer import AbstractPrinter
from slither.core.declarations.function import SolidityFunction
from slither.utils.myprettytable import MyPrettyTable
from slither.utils.function import get_function_id
from slither.core.declarations import Contract, Function


class PrinterWhenNotPaused(AbstractPrinter):

    ARGUMENT = "when-not-paused"
    HELP = "Print entry points that are not can not reach the modifier whenNotPaused"

    WIKI = "https://github.com/trailofbits/slither/wiki/Printer-documentation#when-not-paused"

    @staticmethod
    def _list_functions_not_reaching_modifier(
        contract: Contract, modifier_name: str = "whenNotPaused"
    ) -> List[Function]:
        results: Set[Function] = set()
        for entry_point in contract.functions_entry_points:
            if entry_point.is_constructor or entry_point.view or entry_point.pure:
                continue

            for function in entry_point.all_internal_calls():
                if isinstance(function, SolidityFunction):
                    continue
                if any(modifier.name == modifier_name for modifier in function.modifiers):
                    break
            else:
                results.add(entry_point)

        return results

    def output(self, _filename):
        """
        _filename is not used
        Args:
            _filename(string)
        """

        modifier_name: str = "whenNotPaused"

        txt = ""
        all_tables = []
        for contract in self.slither.contracts:

            txt += f"\n{contract.name}:\n"
            table = MyPrettyTable(["Name", "ID"])

            results = self._list_functions_not_reaching_modifier(contract, modifier_name)
            if results:
                for entry_point in results:
                    function_id = get_function_id(entry_point.solidity_signature)
                    table.add_row([entry_point.solidity_signature, f"{function_id:#0{10}x}"])

                txt += str(table) + "\n"
                all_tables.append((contract.name, table))

        self.info(txt)

        res = self.generate_output(txt)
        for name, table in all_tables:
            res.add_pretty_table(table, name)

        return res
