"""
    Module printing summary of the contract
"""
from slither.core.declarations import Function
from slither.core.source_mapping.source_mapping import Source
from slither.printers.abstract_printer import AbstractPrinter
from slither.utils import output
from slither.utils.output import Output


def _get_source_code(cst: Function) -> str:
    src_mapping: Source = cst.source_mapping
    return " " * src_mapping.starting_column + src_mapping.content


class ConstructorPrinter(AbstractPrinter):
    WIKI = "https://github.com/crytic/slither/wiki/Printer-documentation#constructor-calls"
    ARGUMENT = "constructor-calls"
    HELP = "Print the constructors executed"

    def output(self, _filename: str) -> Output:
        info = ""
        for contract in self.slither.contracts_derived:
            stack_name = []
            stack_definition = []
            cst = contract.constructors_declared
            if cst:
                stack_name.append(contract.name)
                stack_definition.append(_get_source_code(cst))
            for inherited_contract in contract.inheritance:
                cst = inherited_contract.constructors_declared
                if cst:
                    stack_name.append(inherited_contract.name)
                    stack_definition.append(_get_source_code(cst))

            if len(stack_name) > 0:

                info += "\n########" + "#" * len(contract.name) + "########\n"
                info += "####### " + contract.name + " #######\n"
                info += "########" + "#" * len(contract.name) + "########\n\n"
                info += "## Constructor Call Sequence" + "\n"

                for name in stack_name[::-1]:
                    info += "\t- " + name + "\n"
                info += "\n## Constructor Definitions" + "\n"
                count = len(stack_definition) - 1
                while count >= 0:
                    info += "\n### " + stack_name[count] + "\n"
                    info += "\n" + str(stack_definition[count]) + "\n"
                    count = count - 1

        self.info(info)
        res = output.Output(info)
        return res
