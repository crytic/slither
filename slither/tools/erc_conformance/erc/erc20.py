import logging

from slither.core.declarations import Contract
from slither.utils import output

logger = logging.getLogger("Slither-conformance")


def approval_race_condition(contract: Contract, ret: dict[str, list]) -> None:
    increaseAllowance = contract.get_function_from_signature("increaseAllowance(address,uint256)")

    if not increaseAllowance:
        increaseAllowance = contract.get_function_from_signature(
            "safeIncreaseAllowance(address,uint256)"
        )

    if increaseAllowance:
        txt = f"\t[✓] {contract.name} has {increaseAllowance.full_name}"
        logger.info(txt)
    else:
        txt = f"\t[ ] {contract.name} is not protected for the ERC20 approval race condition"
        logger.info(txt)

        lack_of_erc20_race_condition_protection = output.Output(txt)
        lack_of_erc20_race_condition_protection.add(contract)
        ret["lack_of_erc20_race_condition_protection"].append(
            lack_of_erc20_race_condition_protection.data
        )


def check_erc20(
    contract: Contract, ret: dict[str, list], explored: bool | None = None
) -> dict[str, list]:
    if explored is None:
        explored = set()

    explored.add(contract)

    approval_race_condition(contract, ret)

    for derived_contract in contract.derived_contracts:
        check_erc20(derived_contract, ret, explored)

    return ret
