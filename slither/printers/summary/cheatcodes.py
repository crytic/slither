"""
Cheatcode printer

This printer prints the usage of cheatcode in the code.
"""

from slither.printers.abstract_printer import AbstractPrinter
from slither.slithir.operations import HighLevelCall
from slither.utils import output


class CheatcodePrinter(AbstractPrinter):
    ARGUMENT = "cheatcode"

    HELP = """
        Print the usage of (Foundry) cheatcodes in the code.
        For the complete list of Cheatcodes, see https://book.getfoundry.sh/cheatcodes/
    """

    WIKI = "https://github.com/trailofbits/slither/wiki/Printer-documentation#cheatcode"

    def output(self, filename: str) -> output.Output:
        info: str = ""

        try:
            vm = self.slither.get_contract_from_name("Vm").pop()
        except IndexError:
            return output.Output("No contract named VM found")

        for contract in self.slither.contracts_derived:
            # Check that the IS_TEST variable is set. (Only works for Foundry)
            is_test_var = contract.variables_as_dict.get("IS_TEST", None)
            is_test = False
            if is_test_var is not None:
                try:
                    is_test = is_test_var.expression.value == "true"
                except AttributeError:
                    pass

            if not is_test:
                continue

            found_contract: bool = False
            contract_info: str = ""
            for func in contract.functions_declared:
                function_info = f"\t{func}\n"
                found_function: bool = False
                for node in func.nodes:
                    for op in node.all_slithir_operations():
                        if (
                            isinstance(op, HighLevelCall)
                            and op.function.contract == vm
                            and op.function.visibility == "external"
                        ):
                            found_function = True
                            function_info += (
                                f"\t\t{op.function.name} - ({node.source_mapping.to_detailed_str()})\n"
                                f"\t\t{node.expression}\n\n"
                            )

                if found_function:
                    if found_contract is False:
                        contract_info = f"{contract} ({contract.source_mapping.filename.short})\n"
                        found_contract = True

                    contract_info += function_info

            if found_contract:
                info += contract_info

        self.info(info)
        res = output.Output(info)
        return res
