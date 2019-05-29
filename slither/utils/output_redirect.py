import io
import logging
import sys


class StandardOutputRedirect:
    """
    Redirects and captures standard output/errors.
    """
    original_stdout = None
    original_stderr = None

    @staticmethod
    def enable():
        """
        Redirects stdout and/or stderr to a captureable StringIO.
        :param redirect_stdout: True if redirection is desired for stdout.
        :param redirect_stderr: True if redirection is desired for stderr.
        :return: None
        """
        # Redirect stdout
        if StandardOutputRedirect.original_stdout is None:
            StandardOutputRedirect.original_stdout = sys.stdout
            sys.stdout = io.StringIO()

        # Redirect stderr
        if StandardOutputRedirect.original_stderr is None:
            StandardOutputRedirect.original_stderr = sys.stderr
            sys.stderr = io.StringIO()
            root_logger = logging.getLogger()
            root_logger.handlers = [logging.StreamHandler(sys.stderr)]

    @staticmethod
    def disable():
        """
        Disables redirection of stdout/stderr, if previously enabled.
        :return: None
        """
        # If we have a stdout backup, restore it.
        if StandardOutputRedirect.original_stdout is not None:
            sys.stdout.close()
            sys.stdout = StandardOutputRedirect.original_stdout
            StandardOutputRedirect.original_stdout = None

        # If we have an stderr backup, restore it.
        if StandardOutputRedirect.original_stderr is not None:
            sys.stderr.close()
            sys.stderr = StandardOutputRedirect.original_stderr
            StandardOutputRedirect.original_stderr = None

    @staticmethod
    def get_stdout_output():
        """
        Obtains the output from stdout
        :return: Returns stdout output as a string
        """
        sys.stdout.seek(0)
        return sys.stdout.read()

    @staticmethod
    def get_stderr_output():
        """
        Obtains the output from stdout
        :return: Returns stdout output as a string
        """
        sys.stderr.seek(0)
        return sys.stderr.read()