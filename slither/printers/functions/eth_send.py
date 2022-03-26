from typing import Iterator, Tuple, Iterable

from slither.printers.abstract_printer import AbstractPrinter
from slither.utils.myprettytable import MyPrettyTable
from slither.utils.output import Output
from slither.slithir.operations import Operation, Call, HighLevelCall, InternalCall
from slither.core.declarations import Function


def can_send_eth(ir: Operation) -> bool:
    """
    Operation.can_send_eth() is not recursive.
    that's surprising because Function.can_send_eth() and Node.can_send_eth() is.
    this one is as well.
    """
    if isinstance(ir, Call) and ir.can_send_eth():
        return True
    if isinstance(ir, (HighLevelCall, InternalCall)):
        # print(len(ir.function
        return any(can_send_eth(x) for x in ir.function.slithir_operations)
    return False


def callstacks_that_can_send_eth(
    function: Function, stack: Tuple[Operation, ...] = ()
) -> Iterator[Tuple[Operation, ...]]:
    for ir in function.slithir_operations:
        if ir in stack:
            continue
        if can_send_eth(ir):
            next_stack = (*stack, ir)
            if isinstance(ir, (HighLevelCall, InternalCall)):
                for stack in callstacks_that_can_send_eth(ir.function, next_stack):
                    yield stack
            else:
                yield next_stack


def callstacks_to_str(stacks: Iterable[Tuple[Operation, ...]]) -> str:
    lines = []
    for stack in stacks:
        level = 0
        for stack_item in stack:
            if isinstance(stack_item, (HighLevelCall, InternalCall)):
                name = stack_item.function.canonical_name
            else:
                name = str(stack_item.expression)
            lines.append("  " * level + name)
            level += 1

    return "\n".join(lines)


class EthSendPrinter(AbstractPrinter):

    ARGUMENT = "eth-send"
    HELP = "Print all functions that can send ETH and the statements that can send ether"

    WIKI = "https://github.com/trailofbits/slither/wiki/Printer-documentation#eth-send"

    def output(self, _filename: str) -> Output:
        txt = ""
        all_tables = []
        for contract in self.slither.contracts:
            if contract.is_top_level:
                continue
            functions = [f for f in contract.functions if f.can_send_eth()]
            if functions:
                txt += f"\n{contract.name}:\n"
                table = MyPrettyTable(["Name", "Callstack"])
                for function in functions:
                    table.add_row(
                        [
                            f"{function.solidity_signature} {function.visibility}",
                            callstacks_to_str(callstacks_that_can_send_eth(function)),
                        ]
                    )
                txt += str(table) + "\n"
                all_tables.append((contract.name, table))

        self.info(txt)

        res = self.generate_output(txt)
        for name, table in all_tables:
            res.add_pretty_table(table, name)

        return res
