from typing import Mapping

from slither.analyses.data_flow.interval_enhanced.core.state_info import \
    StateInfo


class State:
    def __init__(self, info: Mapping[str, StateInfo]):
        self.info = dict(info)  # Convert to dict to make it mutable

    def __eq__(self, other):
        if not isinstance(other, State):
            return False
        return self.info == other.info

    def __hash__(self):
        """Hash function for State"""
        return hash(tuple(sorted(self.info.items())))

    def deep_copy(self) -> "State":
        """Create a deep copy of the State"""
        copied_info = {key: state_info.deep_copy() for key, state_info in self.info.items()}
        return State(copied_info)
