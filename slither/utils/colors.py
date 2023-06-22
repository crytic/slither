from functools import partial
import platform
import sys


class Colors:  # pylint: disable=too-few-public-methods
    COLORIZATION_ENABLED = True
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    BOLD = "\033[1m"
    END = "\033[0m"


def colorize(color: Colors, txt: str) -> str:
    if Colors.COLORIZATION_ENABLED:
        return f"{color}{txt}{Colors.END}"
    return txt


def enable_windows_virtual_terminal_sequences() -> bool:
    """
    Sets the appropriate flags to enable virtual terminal sequences in a Windows command prompt.
    Reference: https://docs.microsoft.com/en-us/windows/console/console-virtual-terminal-sequences
    """

    try:
        # pylint: disable=import-outside-toplevel
        from ctypes import windll, byref  # type: ignore
        from ctypes.wintypes import DWORD, HANDLE

        kernel32 = windll.kernel32
        virtual_terminal_flag = 0x04  # ENABLE_VIRTUAL_TERMINAL_PROCESSING

        # Obtain our stdout/stderr handles.
        # Reference: https://docs.microsoft.com/en-us/windows/console/getstdhandle
        handle_stdout = kernel32.GetStdHandle(-11)
        handle_stderr = kernel32.GetStdHandle(-12)

        # Loop for each stdout/stderr handle.
        for current_handle in [handle_stdout, handle_stderr]:

            # If we get a null handle, or fail any subsequent calls in this scope, we do not colorize any output.
            if current_handle is None or current_handle == HANDLE(-1):
                return False

            # Try to obtain the current flags for the console.
            current_mode = DWORD()
            if not kernel32.GetConsoleMode(current_handle, byref(current_mode)):
                return False

            # If the virtual terminal sequence processing is not yet enabled, we enable it.
            if (current_mode.value & virtual_terminal_flag) == 0:
                if not kernel32.SetConsoleMode(
                    current_handle, current_mode.value | virtual_terminal_flag
                ):
                    return False
    except Exception:  # pylint: disable=broad-except
        # Any generic failure (possibly from calling these methods on older Windows builds where they do not exist)
        # will fall back onto disabling colorization.
        return False

    return True


def set_colorization_enabled(enabled: bool) -> None:
    """
    Sets the enabled state of output colorization.
    :param enabled: Boolean indicating whether output should be colorized.
    :return: None
    """
    # If color is supposed to be enabled and this is windows, we have to enable console virtual terminal sequences:
    if enabled and platform.system() == "Windows":
        Colors.COLORIZATION_ENABLED = enable_windows_virtual_terminal_sequences()
    else:
        # This is not windows, or colorization is being disabled, so we can adjust the state immediately.
        Colors.COLORIZATION_ENABLED = enabled


green = partial(colorize, Colors.GREEN)
yellow = partial(colorize, Colors.YELLOW)
red = partial(colorize, Colors.RED)
blue = partial(colorize, Colors.BLUE)
magenta = partial(colorize, Colors.MAGENTA)
bold = partial(colorize, Colors.BOLD)

# We enable colorization by default if the output is a tty
set_colorization_enabled(sys.stdout.isatty())
