from slither.exceptions import SlitherException


def convert_subdenomination(value, sub):

    # to allow 0.1 ether conversion
    if value[0:2] == "0x":
        value = float(int(value, 16))
    else:
        value = float(value)
    if sub == 'wei':
        return int(value)
    if sub == 'szabo':
        return int(value * int(1e12))
    if sub == 'finney':
        return int(value * int(1e15))
    if sub == 'ether':
        return int(value * int(1e18))
    if sub == 'seconds':
        return int(value)
    if sub == 'minutes':
        return int(value * 60)
    if sub == 'hours':
        return int(value * 60 * 60)
    if sub == 'days':
        return int(value * 60 * 60 * 24)
    if sub == 'weeks':
        return int(value * 60 * 60 * 24 * 7)
    if sub == 'years':
        return int(value * 60 * 60 * 24 * 7 * 365)

    raise SlitherException(f'Subdemonination conversion impossible {value} {sub}')