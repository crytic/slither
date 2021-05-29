from typing import Optional, Any

from slither import Slither
from slither.rpc.commands.abstract_command import AbstractCommand
from slither.rpc.servers.server_state import ServerState


class AnalysisCommand(AbstractCommand):
    command_id = "ANALYZE"
    requires_prior_analysis = False  # this performs analysis, it does not require prior analysis.

    def execute(self, server_state: ServerState, slither: Optional[Slither], args: Optional[dict]) -> Any:
        # Obtain the target from arguments
        analysis_target = args['target']

        # Perform analysis (TODO: handle custom arguments)
        slither = Slither(analysis_target)

        # Register the analysis with our server for later referencing and return our registration key as a response
        analysis_key = server_state.register_analysis(slither)
        return analysis_key



