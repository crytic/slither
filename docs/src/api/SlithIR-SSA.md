## SSA

Slither possess a Static Single Assignment (SSA) form representation of SlithIR. SSA is a commonly used representation in compilation and static analysis in general. It requires that each variable is assigned at least one time. SSA is a key component for building an efficient data-dependency analysis.

The [SSA printer](../printers/Printer-documentation.md#slithir-ssa) allows to visualize this representation.
