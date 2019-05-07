
def erc_to_signatures(erc):
    return [f'{e[0]}({",".join(e[1])})' for e in erc]


# Final
# https://eips.ethereum.org/EIPS/eip-20
# name, symbolc, decimals are optionals
ERC20 = [('totalSupply', [], 'uint256'),
         ('balanceOf', ['address'], 'uint256'),
         ('transfer', ['address', 'uint256'], 'bool'),
         ('transferFrom', ['address', 'address', 'uint256'], 'bool'),
         ('approve', ['address', 'uint256'], 'bool'),
         ('allowance', ['address', 'address'], 'uint256')]
ERC20_signatures = erc_to_signatures(ERC20)

# Draft
# https://github.com/ethereum/eips/issues/223
ERC223 = [('name', [], 'string'),
          ('symbol', [], 'string'),
          ('decimals', [], 'uint8'),
          ('totalSupply', [], 'uint256'),
          ('balanceOf', ['address'], 'uint256'),
          ('transfer', ['address', 'uint256'], 'bool'),
          ('transfer', ['address', 'uint256', 'bytes'], 'bool'),
          ('transfer', ['address', 'uint256', 'bytes', 'string'], 'bool')]
ERC223_signatures = erc_to_signatures(ERC223)

# Final
# https://eips.ethereum.org/EIPS/eip-165
ERC165 = [('supportsInterface', ['bytes4'], 'bool')]
ERC165_signatures = erc_to_signatures(ERC165)

# Final
# https://eips.ethereum.org/EIPS/eip-721
# Must have ERC165
# name, symbol, tokenURI are optionals
ERC721 = [('balanceOf', ['address'],  'uint256'),
          ('ownerOf', ['uint256'],  'address'),
          ('safeTransferFrom', ['address', 'address', 'uint256', 'bytes'], ''),
          ('safeTransferFrom', ['address', 'address', 'uint256'], ''),
          ('transferFrom', ['address', 'address', 'uint256'], ''),
          ('approve', ['address', 'uint256'], ''),
          ('setApprovalForAll', ['address', 'bool'], ''),
          ('getApproved', ['uint256'], 'address'),
          ('isApprovedForAll', ['address', 'address'], 'bool')] + ERC165
ERC721_signatures = erc_to_signatures(ERC721)

# Final
# https://eips.ethereum.org/EIPS/eip-1820
ERC1820 = [('canImplementInterfaceForAddress', ['bytes32', 'address'], 'bytes32')]
ERC1820_signatures = erc_to_signatures(ERC1820)

# Last Call
# https://eips.ethereum.org/EIPS/eip-777
ERC777 = [('name', [], 'string'),
          ('symbol', [], 'string'),
          ('totalSupply', [], 'uint256'),
          ('balanceOf', ['address'], 'uint256'),
          ('granularity', [], 'uint256'),
          ('defaultOperators', [], 'address[]'),
          ('isOperatorFor', ['address', 'address'], 'bool'),
          ('authorizeOperator', ['address'], ''),
          ('revokeOperator', ['address'], ''),
          ('send', ['address', 'uint256', 'bytes'], ''),
          ('operatorSend', ['address', 'address', 'uint256', 'bytes', 'bytes'], ''),
          ('burn', ['uint256', 'bytes'] , ''),
          ('operatorBurn', ['address', 'uint256', 'bytes', 'bytes'] , '')]
ERC777_signatures = erc_to_signatures(ERC777)