import logging
from typing import Dict, List, Optional

from slither.core.declarations import Contract
from slither.slithir.operations import EventCall
from slither.utils import output

logger = logging.getLogger("Slither-conformance")


def events_safeBatchTransferFrom(contract: Contract, ret: Dict[str, List]) -> None:
    function = contract.get_function_from_signature(
        "safeBatchTransferFrom(address,address,uint256[],uint256[],bytes)"
    )
    events = [
        {
            "name": "TransferSingle",
            "parameters": ["address", "address", "address", "uint256", "uint256"],
        },
        {
            "name": "TransferBatch",
            "parameters": ["address", "address", "address", "uint256[]", "uint256[]"],
        },
    ]

    event_counter_name = 0
    event_counter_parameters = 0
    if function:
        for event in events:
            for ir in function.all_slithir_operations():
                if isinstance(ir, EventCall) and ir.name == event["name"]:
                    event_counter_name += 1
                    if event["parameters"] == [str(a.type) for a in ir.arguments]:
                        event_counter_parameters += 1
    if event_counter_parameters == 1 and event_counter_name == 1:
        txt = "[✓] safeBatchTransferFrom emit TransferSingle or TransferBatch"
        logger.info(txt)
    else:
        txt = "[ ] safeBatchTransferFrom must emit TransferSingle or TransferBatch"
        logger.info(txt)

        erroneous_erc1155_safeBatchTransferFrom_event = output.Output(txt)
        erroneous_erc1155_safeBatchTransferFrom_event.add(contract)
        ret["erroneous_erc1155_safeBatchTransferFrom_event"].append(
            erroneous_erc1155_safeBatchTransferFrom_event.data
        )


def check_erc1155(
    contract: Contract, ret: Dict[str, List], explored: Optional[bool] = None
) -> Dict[str, List]:
    if explored is None:
        explored = set()

    explored.add(contract)

    events_safeBatchTransferFrom(contract, ret)

    for derived_contract in contract.derived_contracts:
        check_erc1155(derived_contract, ret, explored)

    return ret
