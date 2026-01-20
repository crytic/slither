"""
Module printing the C3 linearization order for contract inheritance.

The C3 linearization shows the method resolution order (MRO) which determines:
- Function override order
- Constructor execution order (reverse of linearization)
- Super call resolution
"""

from slither.printers.abstract_printer import AbstractPrinter
from slither.utils.colors import blue, green, yellow


class PrinterC3Linearization(AbstractPrinter):
    ARGUMENT = "c3-linearization"
    HELP = "Print the C3 linearization order for each contract"

    WIKI = "https://github.com/crytic/slither/wiki/Printer-documentation#c3-linearization"

    def output(self, filename):
        """
        Output the C3 linearization order for all contracts.

        Args:
            filename(string): not used
        """
        info = ""
        result = {"linearizations": {}}

        for contract in self.contracts:
            if contract.is_interface:
                continue

            info += blue(f"\nC3 Linearization for {contract.name}\n")
            info += "=" * (24 + len(contract.name)) + "\n"

            # The contract.inheritance is already the C3 linearization order
            linearization = [contract] + list(contract.inheritance)

            result["linearizations"][contract.name] = {
                "order": [],
                "constructor_order": [],
            }

            for i, c in enumerate(linearization):
                # Determine the type label
                if i == 0:
                    label = "[SELF]"
                    color_fn = green
                elif c in contract.immediate_inheritance:
                    label = "[BASE]"
                    color_fn = yellow
                else:
                    label = "[INHERITED]"
                    # Identity function for inherited (no color)
                    def color_fn(x):
                        return x

                # Get source location
                source_loc = ""
                if c.source_mapping and c.source_mapping.lines:
                    source_loc = f" ({c.source_mapping.filename.short}:{c.source_mapping.lines[0]})"

                # Check for constructor
                has_constructor = "✓" if c.constructor else "✗"

                info += f" {i:2}. {color_fn(f'{label:12} {c.name}')}{source_loc}"
                info += f"  [constructor: {has_constructor}]\n"

                result["linearizations"][contract.name]["order"].append(
                    {
                        "index": i,
                        "contract": c.name,
                        "type": label.strip("[]"),
                        "has_constructor": c.constructor is not None,
                        "source": c.source_mapping.filename.short if c.source_mapping else None,
                    }
                )

            # Show constructor execution order (reverse of linearization)
            constructors = [
                (c.name, c.constructor) for c in reversed(linearization) if c.constructor
            ]
            if constructors:
                info += "\n  Constructor Execution Order:\n"
                for i, (name, ctor) in enumerate(constructors, 1):
                    info += f"    {i}. {name}.constructor()\n"
                    result["linearizations"][contract.name]["constructor_order"].append(name)

            info += "\n"

        self.info(info)
        res = self.generate_output(info, additional_fields=result)
        return res
