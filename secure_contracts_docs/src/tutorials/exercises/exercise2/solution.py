from slither import Slither

slither = Slither('coin.sol')

whitelist = ['balanceOf(address)']

for contract in slither.contracts:
    for function in contract.functions:
        if function.full_name in whitelist:
            continue
        if function.is_constructor:
            continue
        if function.visibility in ['public', 'external']:
            if not 'onlyOwner()' in [m.full_name for m in function.modifiers]:
                print(f'{function.full_name} is unprotected!')
