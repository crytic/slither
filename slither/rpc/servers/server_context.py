from slither import Slither
from typing import Optional


class ServerContext:
    def __init__(self):
        # Create our basic LSP state variables
        self.lsp_initialized: bool = False

        # Create our analysis results structure
        self._analysis_results = {}

    def register_analysis(self, slither_instance: Slither) -> int:
        """
        Registers an analysis object with a unique identifier for subsequent operations to be performed on.
        :param slither_instance: The slither analysis instance which we wish to store for subsequent operations to be
        performed on.
        :return: Returns a key which can be used to obtain
        """
        # TODO: Generate a unique, prune old results so we don't bloat maybe? For now only store one instance.
        analysis_id = 0

        # Set our slither instance in our lookup and return the analysis id.
        self._analysis_results[analysis_id] = slither_instance
        return analysis_id

    def get_analysis(self, key: int) -> Optional[Slither]:
        """
        Obtains an analysis object associated with a unique key during a previous registration.
        :param key: The unique key associated with a previously registered analysis.
        :return:
        """
        return self._analysis_results.get(key)
