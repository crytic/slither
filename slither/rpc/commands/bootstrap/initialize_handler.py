from slither.rpc.commands.base_handler import BaseCommandHandler
from typing import Any, List, Union


class InitializeHandler(BaseCommandHandler):
    """
    Handler for the 'initialize' command, which exchanges capability/workspace information.
    Reference: https://microsoft.github.io/language-server-protocol/specifications/specification-3-16/#initialize
    """
    method_name = "initialize"

    @staticmethod
    def process(message_id: Union[int, str, None], params: Any):
        # Verify params is the correct type
        if not isinstance(params, dict):
            raise ValueError("Invalid params supplied. Expected a dictionary/structure type at the top level.")

        # Obtain the workspace folders
        workspace_uris: List[str] = []
        workspace_folders = params.get('workspaceFolders')
        if workspace_folders is not None and isinstance(workspace_folders, list):
            for workspace_folder in workspace_folders:
                if isinstance(workspace_folder, dict):
                    workspace_uri = workspace_folder.get('uri')
                    if workspace_uri is not None and isinstance(workspace_uri, str):
                        workspace_uris.append(workspace_uri)

        # If we couldn't obtain any, try the older deprecated uri param
        if len(workspace_uris) == 0:
            workspace_uri = params.get('rootUri')
            if workspace_uri is not None and isinstance(workspace_uri, str):
                workspace_uris.append(workspace_uri)

        # TODO: Parse client info
        # TODO: Parse client capabilities

        # TODO: Put parsed info into server context
        # TODO: Send a response
