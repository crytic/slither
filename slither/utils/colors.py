from functools import partial


class Colors:
    COLORIZATION_ENABLED = True
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    END = '\033[0m'


def colorize(color, txt):
    if Colors.COLORIZATION_ENABLED:
        return '{}{}{}'.format(color, txt, Colors.END)
    else:
        return txt


def set_colorization_enabled(enabled):
    Colors.COLORIZATION_ENABLED = enabled


green = partial(colorize, Colors.GREEN)
yellow = partial(colorize, Colors.YELLOW)
red = partial(colorize, Colors.RED)
blue = partial(colorize, Colors.BLUE)
magenta = partial(colorize, Colors.MAGENTA)
