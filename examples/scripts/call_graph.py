import os
import logging
import argparse
from slither import Slither
from slither.printers.all_printers import PrinterCallGraph
from slither.core.declarations.function import Function

logging.basicConfig()
logging.getLogger("Slither").setLevel(logging.INFO)
logging.getLogger("Printers").setLevel(logging.INFO)


class PrinterCallGraphStateChange(PrinterCallGraph):
    def _process_function(
        self,
        contract,
        function,
        contract_functions,
        contract_calls,
        solidity_functions,
        solidity_calls,
        external_calls,
        all_contracts,
    ):
        if function.view or function.pure:
            return
        super()._process_function(
            contract,
            function,
            contract_functions,
            contract_calls,
            solidity_functions,
            solidity_calls,
            external_calls,
            all_contracts,
        )

    def _process_internal_call(
        self, contract, function, internal_call, contract_calls, solidity_functions, solidity_calls
    ):
        if isinstance(internal_call, Function):
            if internal_call.view or internal_call.pure:
                return
        super()._process_internal_call(
            contract, function, internal_call, contract_calls, solidity_functions, solidity_calls
        )

    def _process_external_call(
        self, contract, function, external_call, contract_functions, external_calls, all_contracts
    ):
        if isinstance(external_call[1], Function):
            if external_call[1].view or external_call[1].pure:
                return
        super()._process_external_call(
            contract, function, external_call, contract_functions, external_calls, all_contracts
        )


def parse_args():
    """
    """
    parser = argparse.ArgumentParser(
        description="Call graph printer. Similar to --print call-graph, but without printing the view/pure functions",
        usage="call_graph.py filename",
    )

    parser.add_argument(
        "filename", help="The filename of the contract or truffle directory to analyze."
    )

    parser.add_argument("--solc", help="solc path", default="solc")

    return parser.parse_args()


def main():

    args = parse_args()
    slither = Slither(args.filename, is_truffle=os.path.isdir(args.filename), solc=args.solc)

    slither.register_printer(PrinterCallGraphStateChange)

    slither.run_printers()


if __name__ == "__main__":
    main()
