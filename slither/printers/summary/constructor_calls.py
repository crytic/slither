"""
    Module printing summary of the contract
"""
from slither.printers.abstract_printer import AbstractPrinter
from slither.utils import output


class ConstructorPrinter(AbstractPrinter):
    WIKI = (
        "https://github.com/crytic/slither/wiki/Printer-documentation#constructor-calls"
    )
    ARGUMENT = "constructor-calls"
    HELP = "Print the constructors executed"

    def _get_soruce_code(self, cst):
        src_mapping = cst.source_mapping
        content = self.slither.source_code[src_mapping["filename_absolute"]]
        start = src_mapping["start"]
        end = src_mapping["start"] + src_mapping["length"]
        initial_space = src_mapping["starting_column"]
        return " " * initial_space + content[start:end]

    def output(self, _filename):
        info = ""
        for contract in self.slither.contracts_derived:
            stack_name = []
            stack_definition = []
            cst = contract.constructors_declared
            if cst:
                stack_name.append(contract.name)
                stack_definition.append(self._get_soruce_code(cst))
            for inherited_contract in contract.inheritance:
                cst = inherited_contract.constructors_declared
                if cst:
                    stack_name.append(inherited_contract.name)
                    stack_definition.append(self._get_soruce_code(cst))

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
