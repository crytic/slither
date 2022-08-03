from collections import namedtuple
from typing import List

ERC = namedtuple("ERC", ["name", "parameters", "return_type", "view", "required", "events"])
ERC_EVENT = namedtuple("ERC_EVENT", ["name", "parameters", "indexes"])


def erc_to_signatures(erc: List[ERC]):
    """
    Return the list of mandatory signatures
    :param erc:
    :return:
    """
    return [f'{e.name}({",".join(e.parameters)})' for e in erc if e.required]


# Final
# https://eips.ethereum.org/EIPS/eip-20

ERC20_transfer_event = ERC_EVENT("Transfer", ["address", "address", "uint256"], [True, True, False])
ERC20_approval_event = ERC_EVENT("Approval", ["address", "address", "uint256"], [True, True, False])
ERC20_EVENTS = [ERC20_transfer_event, ERC20_approval_event]

ERC20 = [
    ERC("totalSupply", [], "uint256", True, True, []),
    ERC("balanceOf", ["address"], "uint256", True, True, []),
    ERC("transfer", ["address", "uint256"], "bool", False, True, [ERC20_transfer_event]),
    ERC(
        "transferFrom",
        ["address", "address", "uint256"],
        "bool",
        False,
        True,
        [ERC20_transfer_event],
    ),
    ERC("approve", ["address", "uint256"], "bool", False, True, [ERC20_approval_event]),
    ERC("allowance", ["address", "address"], "uint256", True, True, []),
]

ERC20_OPTIONAL = [
    ERC("name", [], "string", True, False, []),
    ERC("symbol", [], "string", True, False, []),
    ERC("decimals", [], "uint8", True, False, []),
]

ERC20 = ERC20 + ERC20_OPTIONAL

ERC20_signatures = erc_to_signatures(ERC20)

# Draft
# https://github.com/ethereum/eips/issues/223

ERC223_transfer_event = ERC_EVENT(
    "Transfer", ["address", "address", "uint256", "bytes"], [True, True, False, False]
)

ERC223_EVENTS = [ERC223_transfer_event]

ERC223 = [
    ERC("name", [], "string", True, True, []),
    ERC("symbol", [], "string", True, True, []),
    ERC("decimals", [], "uint8", True, True, []),
    ERC("totalSupply", [], "uint256", True, True, []),
    ERC("balanceOf", ["address"], "uint256", True, True, []),
    ERC("transfer", ["address", "uint256"], "bool", False, True, [ERC223_transfer_event]),
    ERC(
        "transfer",
        ["address", "uint256", "bytes"],
        "bool",
        False,
        True,
        [ERC223_transfer_event],
    ),
    ERC(
        "transfer",
        ["address", "uint256", "bytes", "string"],
        "bool",
        False,
        True,
        [ERC223_transfer_event],
    ),
]
ERC223_signatures = erc_to_signatures(ERC223)

# Final
# https://eips.ethereum.org/EIPS/eip-165

ERC165_EVENTS: List = []

ERC165 = [ERC("supportsInterface", ["bytes4"], "bool", True, True, [])]
ERC165_signatures = erc_to_signatures(ERC165)

# Final
# https://eips.ethereum.org/EIPS/eip-721
# Must have ERC165

ERC721_transfer_event = ERC_EVENT("Transfer", ["address", "address", "uint256"], [True, True, True])
ERC721_approval_event = ERC_EVENT("Approval", ["address", "address", "uint256"], [True, True, True])
ERC721_approvalforall_event = ERC_EVENT(
    "ApprovalForAll", ["address", "address", "bool"], [True, True, False]
)
ERC721_EVENTS = [
    ERC721_transfer_event,
    ERC721_approval_event,
    ERC721_approvalforall_event,
]

ERC721 = [
    ERC("balanceOf", ["address"], "uint256", True, True, []),
    ERC("ownerOf", ["uint256"], "address", True, True, []),
    ERC(
        "safeTransferFrom",
        ["address", "address", "uint256", "bytes"],
        "",
        False,
        True,
        [ERC721_transfer_event],
    ),
    ERC(
        "safeTransferFrom",
        ["address", "address", "uint256"],
        "",
        False,
        True,
        [ERC721_transfer_event],
    ),
    ERC(
        "transferFrom",
        ["address", "address", "uint256"],
        "",
        False,
        True,
        [ERC721_transfer_event],
    ),
    ERC("approve", ["address", "uint256"], "", False, True, [ERC721_approval_event]),
    ERC(
        "setApprovalForAll",
        ["address", "bool"],
        "",
        False,
        True,
        [ERC721_approvalforall_event],
    ),
    ERC("getApproved", ["uint256"], "address", True, True, []),
    ERC("isApprovedForAll", ["address", "address"], "bool", True, True, []),
] + ERC165

ERC721_OPTIONAL = [
    ERC("name", [], "string", True, False, []),
    ERC("symbol", [], "string", False, False, []),
    ERC("tokenURI", ["uint256"], "string", False, False, []),
]

ERC721 = ERC721 + ERC721_OPTIONAL

ERC721_signatures = erc_to_signatures(ERC721)

# Final
# https://eips.ethereum.org/EIPS/eip-1820
ERC1820_EVENTS: List = []
ERC1820 = [
    ERC(
        "canImplementInterfaceForAddress",
        ["bytes32", "address"],
        "bytes32",
        True,
        True,
        [],
    )
]
ERC1820_signatures = erc_to_signatures(ERC1820)

# Last Call
# https://eips.ethereum.org/EIPS/eip-777
ERC777_sent_event = ERC_EVENT(
    "Sent",
    ["address", "address", "address", "uint256", "bytes", "bytes"],
    [True, True, True, False, False, False],
)
ERC777_minted_event = ERC_EVENT(
    "Minted",
    ["address", "address", "uint256", "bytes", "bytes"],
    [True, True, False, False, False],
)
ERC777_burned_event = ERC_EVENT(
    "Burned",
    ["address", "address", "uint256", "bytes", "bytes"],
    [True, True, False, False, False],
)
ERC777_authorizedOperator_event = ERC_EVENT(
    "AuthorizedOperator", ["address", "address"], [True, True]
)
ERC777_revokedoperator_event = ERC_EVENT("RevokedOperator", ["address", "address"], [True, True])
ERC777_EVENTS = [
    ERC777_sent_event,
    ERC777_minted_event,
    ERC777_burned_event,
    ERC777_authorizedOperator_event,
    ERC777_revokedoperator_event,
]

ERC777 = [
    ERC("name", [], "string", True, True, []),
    ERC("symbol", [], "string", True, True, []),
    ERC("totalSupply", [], "uint256", True, True, []),
    ERC("balanceOf", ["address"], "uint256", True, True, []),
    ERC("granularity", [], "uint256", True, True, []),
    ERC("defaultOperators", [], "address[]", True, True, []),
    ERC("isOperatorFor", ["address", "address"], "bool", True, True, []),
    ERC(
        "authorizeOperator",
        ["address"],
        "",
        False,
        True,
        [ERC777_authorizedOperator_event],
    ),
    ERC("revokeOperator", ["address"], "", False, True, [ERC777_revokedoperator_event]),
    ERC("send", ["address", "uint256", "bytes"], "", False, True, [ERC777_sent_event]),
    ERC(
        "operatorSend",
        ["address", "address", "uint256", "bytes", "bytes"],
        "",
        False,
        True,
        [ERC777_sent_event],
    ),
    ERC("burn", ["uint256", "bytes"], "", False, True, [ERC777_burned_event]),
    ERC(
        "operatorBurn",
        ["address", "uint256", "bytes", "bytes"],
        "",
        False,
        True,
        [ERC777_burned_event],
    ),
]
ERC777_signatures = erc_to_signatures(ERC777)

# Final
# https://eips.ethereum.org/EIPS/eip-1155
# Must have ERC165

ERC1155_transfersingle_event = ERC_EVENT(
    "TransferSingle",
    ["address", "address", "address", "uint256", "uint256"],
    [True, True, True, False, False],
)

ERC1155_transferbatch_event = ERC_EVENT(
    "TransferBatch",
    ["address", "address", "address", "uint256[]", "uint256[]"],
    [True, True, True, False, False],
)

ERC1155_approvalforall_event = ERC_EVENT(
    "ApprovalForAll",
    ["address", "address", "bool"],
    [True, True, False],
)

ERC1155_uri_event = ERC_EVENT(
    "URI",
    ["string", "uint256"],
    [False, True],
)

ERC1155_EVENTS = [
    ERC1155_transfersingle_event,
    ERC1155_transferbatch_event,
    ERC1155_approvalforall_event,
    ERC1155_uri_event,
]

ERC1155 = [
    ERC(
        "safeTransferFrom",
        ["address", "address", "uint256", "uint256", "bytes"],
        "",
        False,
        True,
        [ERC1155_transfersingle_event],
    ),
    ERC(
        "safeBatchTransferFrom",
        ["address", "address", "uint256[]", "uint256[]", "bytes"],
        "",
        False,
        True,
        [],
    ),
    ERC("balanceOf", ["address", "uint256"], "uint256", True, True, []),
    ERC("balanceOfBatch", ["address[]", "uint256[]"], "uint256[]", True, True, []),
    ERC("setApprovalForAll", ["address", "bool"], "", False, True, [ERC1155_approvalforall_event]),
    ERC("isApprovedForAll", ["address", "address"], "bool", True, True, []),
] + ERC165

ERC1155_TOKEN_RECEIVER = [
    ERC(
        "onERC1155Received",
        ["address", "address", "uint256", "uint256", "bytes"],
        "bytes4",
        False,
        False,
        [],
    ),
    ERC(
        "onERC1155BatchReceived",
        ["address", "address", "uint256[]", "uint256[]", "bytes"],
        "bytes4",
        False,
        False,
        [],
    ),
]

ERC1155_METADATA = [ERC("uri", ["uint256"], "string", True, False, [])]

ERC1155 = ERC1155 + ERC1155_TOKEN_RECEIVER + ERC1155_METADATA

ERC1155_signatures = erc_to_signatures(ERC1155)

# Review
# https://eips.ethereum.org/EIPS/eip-2612
# Must have ERC20

ERC2612_EVENTS = []
ERC2612 = [
    ERC(
        "permit",
        ["address", "address", "uint256", "uint256", "uint8", "bytes32", "bytes32"],
        "",
        False,
        True,
        [],
    ),
    ERC("nonces", ["address"], "uint256", True, True, []),
    ERC("DOMAIN_SEPARATOR", [], "bytes32", True, True, []),
] + ERC20

ERC2612_signatures = erc_to_signatures(ERC2612)

# Review
# https://eips.ethereum.org/EIPS/eip-1363
# Must have ERC20 and ERC165

ERC1363_EVENTS = []
ERC1363 = (
    [
        ERC("transferAndCall", ["address", "uint256"], "bool", False, True, []),
        ERC("transferAndCall", ["address", "uint256", "bytes"], "bool", False, True, []),
        ERC("transferFromAndCall", ["address", "address", "uint256"], "bool", False, True, []),
        ERC(
            "transferFromAndCall",
            ["address", "address", "uint256", "bytes"],
            "bool",
            False,
            True,
            [],
        ),
        ERC("approveAndCall", ["address", "uint256"], "bool", False, True, []),
        ERC("approveAndCall", ["address", "uint256", "bytes"], "bool", False, True, []),
    ]
    + ERC20
    + ERC165
)

ERC1363_signatures = erc_to_signatures(ERC1363)

# Review
# https://eips.ethereum.org/EIPS/eip-4524
# Must have ERC20 and ERC165

ERC4524_EVENTS = []
ERC4524 = (
    [
        ERC("safeTransfer", ["address", "uint256"], "bool", False, True, []),
        ERC("safeTransfer", ["address", "uint256", "bytes"], "bool", False, True, []),
        ERC("safeTransferFrom", ["address", "address", "uint256"], "bool", False, True, []),
        ERC(
            "safeTransferFrom", ["address", "address", "uint256", "bytes"], "bool", False, True, []
        ),
    ]
    + ERC20
    + ERC165
)

ERC4524_signatures = erc_to_signatures(ERC4524)

# Final
# https://eips.ethereum.org/EIPS/eip-4626
# Must have ERC20

ERC4626_deposit_event = ERC_EVENT(
    "Deposit",
    ["address", "address", "uint256", "uint256"],
    [True, True, False, False],
)

ERC4626_withdraw_event = ERC_EVENT(
    "Withdraw",
    ["address", "address", "address", "uint256", "uint256"],
    [True, True, True, False, False],
)

ERC4626_EVENTS = [
    ERC4626_deposit_event,
    ERC4626_withdraw_event,
]

ERC4626 = [
    ERC("asset", [], "address", True, True, []),
    ERC("totalAssets", [], "uint256", True, True, []),
    ERC("convertToShares", ["uint256"], "uint256", True, True, []),
    ERC("convertToAssets", ["uint256"], "uint256", True, True, []),
    ERC("maxDeposit", ["address"], "uint256", True, True, []),
    ERC("previewDeposit", ["uint256"], "uint256", True, True, []),
    ERC("deposit", ["uint256", "address"], "uint256", False, True, [ERC4626_deposit_event]),
    ERC("maxMint", ["address"], "uint256", True, True, []),
    ERC("previewMint", ["uint256"], "uint256", True, True, []),
    ERC("mint", ["uint256", "address"], "uint256", False, True, [ERC4626_deposit_event]),
    ERC("maxWithdraw", ["address"], "uint256", True, True, []),
    ERC("previewWithdraw", ["uint256"], "uint256", True, True, []),
    ERC(
        "withdraw",
        ["uint256", "address", "address"],
        "uint256",
        False,
        True,
        [ERC4626_withdraw_event],
    ),
    ERC("maxRedeem", ["address"], "uint256", True, True, []),
    ERC("previewRedeem", ["uint256"], "uint256", True, True, []),
    ERC(
        "redeem",
        ["uint256", "address", "address"],
        "uint256",
        False,
        True,
        [ERC4626_withdraw_event],
    ),
] + ERC20

ERC4626_signatures = erc_to_signatures(ERC4626)

ERCS = {
    "ERC20": (ERC20, ERC20_EVENTS),
    "ERC223": (ERC223, ERC223_EVENTS),
    "ERC165": (ERC165, ERC165_EVENTS),
    "ERC721": (ERC721, ERC721_EVENTS),
    "ERC1820": (ERC1820, ERC1820_EVENTS),
    "ERC777": (ERC777, ERC777_EVENTS),
    "ERC1155": (ERC1155, ERC1155_EVENTS),
    "ERC2612": (ERC2612, ERC2612_EVENTS),
    "ERC1363": (ERC1363, ERC1363_EVENTS),
    "ERC4524": (ERC4524, ERC4524_EVENTS),
    "ERC4626": (ERC4626, ERC4626_EVENTS),
}
