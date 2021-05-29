import argparse

import logging

from slither.rpc.servers.console_server import ConsoleServer
from slither.rpc.servers.network_server import NetworkServer

logging.basicConfig()
logging.getLogger("Slither").setLevel(logging.INFO)


def parse_args() -> argparse.Namespace:
    """
    Parse the underlying arguments for the program.
    :return: Returns the arguments for the program.
    """
    # Initialize our argument parser
    parser = argparse.ArgumentParser(
        description="slither-rpc",
        usage="slither-rpc [options]",
    )

    # We want to offer a switch to communicate over a network socket rather than stdin/stdout.
    parser.add_argument(
        "--network", help="Indicates that the RPC server should use a network socket rather than stdin/stdout.",
        action='store_true',
        default=False
    )

    # TODO: We should add additional arguments for host/port binding for the --network option.

    return parser.parse_args()


def main() -> None:
    """
    The main entry point for the application. Parses arguments and starts the RPC server.
    :return: None
    """
    # Parse all arguments
    args = parse_args()

    # Determine which server provider to use.
    if args.network:
        server = NetworkServer()
    else:
        server = ConsoleServer()

    # Begin processing commands
    server.main_loop()


if __name__ == "__main__":
    main()
