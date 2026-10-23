"""
Module printing the echidna/manticore-verifier properties

Properties are functions with a name starting with `echidna_` or `crytic_`.
The printer outputs a markdown-compatible table that can be used to track
the properties and their testing results.
"""

from slither.printers.abstract_printer import AbstractPrinter
from slither.utils.output import Output

# Prefixes identifying property functions, see
# https://github.com/crytic/slither/issues/606
# and the naming convention detector
PROPERTY_PREFIXES = ("echidna_", "crytic_")


def _is_property_function(function) -> bool:
    return function.name.startswith(PROPERTY_PREFIXES)


class PropertiesPrinter(AbstractPrinter):
    ARGUMENT = "properties"
    HELP = "Print the echidna/manticore-verifier properties as a markdown table"

    WIKI = "https://github.com/trailofbits/slither/wiki/Printer-documentation#properties"

    def output(self, _filename: str) -> Output:
        """
        _filename is not used
        Args:
            _filename(string)
        """

        def _markdown_link(function) -> str:
            link = function.source_mapping.to_markdown(self.slither.markdown_root)
            return f"[{function.name}]({link})"

        header = ["Description", "Name", "Contract", "Result"]
        rows = []
        for contract in self.compilation_unit.contracts_derived:
            for function in contract.functions:
                if _is_property_function(function):
                    # Slither does not parse natspec yet, the description is left
                    # empty for the user to fill in
                    rows.append(["", _markdown_link(function), contract.name, ""])

        lines = [
            "| " + " | ".join(header) + " |",
            "|" + "|".join(["---"] * len(header)) + "|",
        ]
        lines += ["| " + " | ".join(row) + " |" for row in rows]
        txt = "\n".join(lines) + "\n"

        self.info(txt)

        return self.generate_output(txt)
