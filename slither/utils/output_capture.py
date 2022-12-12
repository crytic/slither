import io
import logging
import sys


class CapturingStringIO(io.StringIO):
    """
    I/O implementation which captures output, and optionally mirrors it to the original I/O stream it replaces.
    """

    def __init__(self, original_io=None):
        super().__init__()
        self.original_io = original_io

    def write(self, s):
        super().write(s)
        if self.original_io:
            self.original_io.write(s)


class StandardOutputCapture:
    """
    Redirects and captures standard output/errors.
    """

    original_stdout = None
    original_stderr = None
    original_logger_handlers = None

    @staticmethod
    def enable(block_original: bool = True) -> None:
        """
        Redirects stdout and stderr to a capturable StringIO.
        :param block_original: If True, blocks all output to the original stream. If False, duplicates output.
        :return: None
        """
        # Redirect stdout
        if StandardOutputCapture.original_stdout is None:
            StandardOutputCapture.original_stdout = sys.stdout
            sys.stdout = CapturingStringIO(
                None if block_original else StandardOutputCapture.original_stdout
            )

        # Redirect stderr
        if StandardOutputCapture.original_stderr is None:
            StandardOutputCapture.original_stderr = sys.stderr
            sys.stderr = CapturingStringIO(
                None if block_original else StandardOutputCapture.original_stderr
            )

            # Backup and swap root logger handlers
            root_logger = logging.getLogger()
            StandardOutputCapture.original_logger_handlers = root_logger.handlers
            root_logger.handlers = [logging.StreamHandler(sys.stderr)]

    @staticmethod
    def disable() -> None:
        """
        Disables redirection of stdout/stderr, if previously enabled.
        :return: None
        """
        # If we have a stdout backup, restore it.
        if StandardOutputCapture.original_stdout is not None:
            sys.stdout.close()
            sys.stdout = StandardOutputCapture.original_stdout
            StandardOutputCapture.original_stdout = None

        # If we have an stderr backup, restore it.
        if StandardOutputCapture.original_stderr is not None:
            sys.stderr.close()
            sys.stderr = StandardOutputCapture.original_stderr
            StandardOutputCapture.original_stderr = None

        # Restore our logging handlers
        if StandardOutputCapture.original_logger_handlers is not None:
            root_logger = logging.getLogger()
            root_logger.handlers = StandardOutputCapture.original_logger_handlers
            StandardOutputCapture.original_logger_handlers = None

    @staticmethod
    def get_stdout_output() -> str:
        """
        Obtains the output from the currently set stdout
        :return: Returns stdout output as a string
        """
        sys.stdout.seek(0)
        return sys.stdout.read()

    @staticmethod
    def get_stderr_output() -> str:
        """
        Obtains the output from the currently set stderr
        :return: Returns stderr output as a string
        """
        sys.stderr.seek(0)
        return sys.stderr.read()
