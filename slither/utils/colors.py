class Colors:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    END = '\033[0m'

def green(txt):
    return Colors.GREEN + txt + Colors.END
def yellow(txt):
    return Colors.YELLOW + txt + Colors.END
def red(txt):
    return Colors.RED + txt + Colors.END
def blue(txt):
    return Colors.BLUE + txt + Colors.END
def magenta(txt):
    return Colors.MAGENTA + txt + Colors.END

