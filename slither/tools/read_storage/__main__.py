"""
Tool to read on-chain storage from EVM
"""
import json
from pathlib import Path
from typing import Annotated, List, Optional

import typer

from slither import Slither
from slither.exceptions import SlitherError
import slither.tools.read_storage as rs
from slither.__main__ import app
from slither.utils.command_line import SlitherState, SlitherApp, GroupWithCrytic


read_storage: SlitherApp = SlitherApp()
app.add_typer(read_storage, name="read-storage")


@read_storage.callback(cls=GroupWithCrytic)
def main(
    ctx: typer.Context,
    contract_source: Annotated[
        List[str],
        typer.Argument(
            ...,
            help="The deployed contract address if verified on etherscan or prepend project "
            "directory for unverified contracts.",
        ),
    ],
    variable_name: Annotated[
        Optional[str],
        typer.Option(
            "--variable-name", help="The name of the variable whose value will be returned."
        ),
    ] = None,
    rpc_url: Annotated[
        Optional[str], typer.Option("--rpc-url", help="An endpoint for web3 requests.")
    ] = None,
    key: Annotated[
        Optional[str],
        typer.Option(
            "--key", help="The key/index whose value will be returned from a mapping or array."
        ),
    ] = None,
    deep_key: Annotated[
        Optional[str],
        typer.Option(
            "--deep-key",
            help="The key/index whose value will be returned from a deep mapping or multidimensional array.",
        ),
    ] = None,
    struct_var: Annotated[
        Optional[str],
        typer.Option(
            "--struct-var",
            help="The name of the variable whose value will be returned from a struct.",
        ),
    ] = None,
    storage_address: Annotated[
        Optional[str],
        typer.Option(
            "--storage-address",
            help="The address of the storage contract if a proxy pattern is used.",
        ),
    ] = None,
    contract_name: Annotated[
        Optional[str], typer.Option("--contract-name", help="The name of the logic contract.")
    ] = None,
    value: Annotated[
        bool, typer.Option("--value", help="Toggle used to include values in output.", is_flag=True)
    ] = False,
    table: Annotated[
        bool, typer.Option("--table", help="Print table view of storage layout.", is_flag=True)
    ] = False,
    silent: Annotated[
        bool, typer.Option("--silent", help="Silence log outputs.", is_flag=True)
    ] = False,
    max_depth: Annotated[
        int, typer.Option("--max-depth", help="Max depth to search in data structure.")
    ] = 20,
    block: Annotated[
        str,
        typer.Option(
            "--block",
            help="The block number to read storage from. Requires an archive node to be provided as "
            "the RPC url.",
        ),
    ] = "latest",
    unstructured: Annotated[
        bool,
        typer.Option("--unstructured", help="Include unstructured storage slots.", is_flag=True),
    ] = False,
) -> None:
    """Read a variable's value from storage for a deployed contract.

    To retrieve a single variable's value:
        slither read-storage $TARGET address --variable-name $NAME
    To retrieve a contract's storage layout:
        slither read-storage $TARGET address --contract-name $NAME --json storage_layout.json
    To retrieve a contract's storage layout and values:
        slither read-storage $TARGET address --contract-name $NAME --json storage_layout.json --value
    """

    state = ctx.ensure_object(SlitherState)

    if len(contract_source) == 2:
        # Source code is file.sol or project directory
        source_code, target = contract_source
        slither = Slither(source_code, **state)
    else:
        # Source code is published and retrieved via etherscan
        target = contract_source[0]
        slither = Slither(target, **state)

    if contract_name:
        contracts = slither.get_contract_from_name(contract_name)
        if len(contracts) == 0:
            raise SlitherError(f"Contract {contract_name} not found.")
    else:
        contracts = slither.contracts

    rpc_info = None
    if rpc_url:
        valid = ["latest", "earliest", "pending", "safe", "finalized"]
        block = block if block in valid else int(block)
        rpc_info = rs.RpcInfo(rpc_url, block)

    srs = rs.SlitherReadStorage(contracts, max_depth, rpc_info)
    srs.unstructured = unstructured
    # Remove target prefix e.g. rinkeby:0x0 -> 0x0.
    address = target[target.find(":") + 1 :]
    # Default to implementation address unless a storage address is given.
    if not storage_address:
        storage_address = address
    srs.storage_address = storage_address

    if variable_name:
        # Use a lambda func to only return variables that have same name as target.
        # x is a tuple (`Contract`, `StateVariable`).
        srs.get_all_storage_variables(lambda x: bool(x[1].name == variable_name))
        # FIXME: Dirty way of passing all needed values.
        srs.get_target_variables(**locals())
    else:
        srs.get_all_storage_variables()
        srs.get_storage_layout()

    # To retrieve slot values an rpc url is required.
    if value:
        assert rpc_url
        srs.walk_slot_info(srs.get_slot_values)

    if table:
        srs.walk_slot_info(srs.convert_slot_info_to_rows)
        print(srs.table)

    from slither.utils.output import OutputFormat

    if state.get("output_format") == OutputFormat.JSON:
        output_file = state.get("output_file")
        if output_file != Path("-"):
            with open(output_file, "w", encoding="utf-8") as file:
                slot_infos_json = srs.to_json()
                json.dump(slot_infos_json, file, indent=4)


if __name__ == "__main__":
    read_storage()
