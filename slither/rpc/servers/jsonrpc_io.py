import json
import re
from threading import Lock
from typing import Any, Optional, BinaryIO, Tuple, List, Union

CONTENT_LENGTH_REGEX = re.compile("Content-Length:\s+(\d+)\s*", re.IGNORECASE)

class JsonRpcIo:
    """
    Provides IO for Language Server Protocol JSON-RPC over generic file handles.

    Target: Language Server Protocol 3.16
    https://microsoft.github.io/language-server-protocol/specifications/specification-3-16/
    """
    def __init__(self, read_file_handle: BinaryIO, write_file_handle: BinaryIO):
        self._read_file_handle = read_file_handle
        self._write_file_handle = write_file_handle
        self._read_lock = Lock()
        self._write_lock = Lock()

    def read(self) -> Union[Tuple[List[str], Any], None]:
        """
        Attempts to read a message from the underlying file handle and deserialize it.
        :return: Returns a tuple(headers, body) if a message was available, returns None otherwise.
        """
        # TODO: We'll likely want to add some proper exception handling logic here.
        with self._read_lock:
            # Attempt to read headers, searching for Content-Length in the process
            headers = []
            content_length = None
            while True:
                # Read a line, stop reading if one was not available
                line = self._read_file_handle.readline()
                if line is None:
                    break

                # If stripping it results in no remaining content, then it should be the final \r\n string.
                line = line.decode('utf-8')
                if not line.strip():
                    break

                # Add the line to our list of headers
                headers.append(line)

                # See if this line is the content-length header
                match = CONTENT_LENGTH_REGEX.match(line)
                if match:
                    match = match.group()
                    if len(match) > 0:
                        assert content_length is None, "More than one Content-Length header should not be received."
                        content_length = int(match[0])

            # If we didn't receive a content-length header, return None and try to skip
            # TODO: We probably want to send the appropriate error code back in the future.
            if content_length is None:
                return None

            # Next we'll want to read our body
            body = self._read_file_handle.read(content_length)
            body = json.loads(body.decode('utf-8'))
            return headers, body


    def write(self, data: Optional[Any]) -> None:
        """
        Serializes the provided data as JSON and sends it over the underlying file handle.
        :param data: The object to serialize as JSON and write to the underlying file handle.
        :return: None
        """
        # TODO: We'll likely want to add some exception handling logic here.
        with self._write_lock:
            # The default encoding type specified is UTF-8, we encode now to determine content-length header contents.
            encoded_json_data = json.dumps(data).encode('utf-8')

            # Construct our headers. Headers are delimited by '\r\n'. This is also the case for the headers+body.
            # Note: Although Content-Type defaults to the value below, we remain explicit to be safe.
            headers = (
            f"Content-Length: {len(encoded_json_data)}\r\n"
            "Content-Type: application/vscode-jsonrpc; charset=utf-8\r\n"
            "\r\n").encode('utf-8')

            # Write our data and flush it to our handle
            self._write_file_handle.write(headers + encoded_json_data)
            self._write_file_handle.flush()
