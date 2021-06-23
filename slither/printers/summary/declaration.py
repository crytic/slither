from slither.printers.abstract_printer import AbstractPrinter
from slither.utils.source_mapping import get_definition, get_implementation, get_references


class Declaration(AbstractPrinter):
    ARGUMENT = "decl"
    HELP = "TODO"

    WIKI = "TODO"

    def output(self, _filename):
        """
        _filename is not used
        Args:
            _filename(string)
        """

        txt = ""
        for compilation_unit in self.slither.compilation_units:
            txt += "\n# Contracts\n"
            for contract in compilation_unit.contracts:
                txt += f"# {contract.name}\n"
                txt += f"\t- Declaration: {get_definition(contract, compilation_unit.core.crytic_compile).detailled_str()}\n"
                txt += f"\t- Implementation: {get_implementation(contract).detailled_str()}\n"
                txt += f"\t- References: {[x.detailled_str() for x in get_references(contract)]}\n"

                txt += "\n\t## Function\n"

                for func in contract.functions:
                    txt += f"\t\t- {func.canonical_name}\n"
                    txt += f"\t\t\t- Declaration: {get_definition(func, compilation_unit.core.crytic_compile).detailled_str()}\n"
                    txt += f"\t\t\t- Implementation: {get_implementation(func).detailled_str()}\n"
                    txt += (
                        f"\t\t\t- References: {[x.detailled_str() for x in get_references(func)]}\n"
                    )

                txt += "\n\t## State variables\n"

                for var in contract.state_variables:
                    txt += f"\t\t- {var.name}\n"
                    txt += f"\t\t\t- Declaration: {get_definition(var, compilation_unit.core.crytic_compile).detailled_str()}\n"
                    txt += f"\t\t\t- Implementation: {get_implementation(var).detailled_str()}\n"
                    txt += (
                        f"\t\t\t- References: {[x.detailled_str() for x in get_references(var)]}\n"
                    )

                txt += "\n\t## Structures\n"

                for st in contract.structures:
                    txt += f"\t\t- {st.name}\n"
                    txt += f"\t\t\t- Declaration: {get_definition(st, compilation_unit.core.crytic_compile).detailled_str()}\n"
                    txt += f"\t\t\t- Implementation: {get_implementation(st).detailled_str()}\n"
                    txt += (
                        f"\t\t\t- References: {[x.detailled_str() for x in get_references(st)]}\n"
                    )

        self.info(txt)
        res = self.generate_output(txt)
        return res
