from collections import defaultdict


class Context:
    def __init__(self) -> None:
        super().__init__()
        self._context: dict = {"MEMBERS": defaultdict(None)}

    @property
    def context(self) -> dict:
        """
        Dict used by analysis
        """
        return self._context
