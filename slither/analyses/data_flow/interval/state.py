from typing import Mapping

from slither.analyses.data_flow.interval.info import IntervalInfo


class IntervalState:
    def __init__(self, info: Mapping[str, IntervalInfo]):
        self.info = dict(info)  # Convert to dict to make it mutable

    def __eq__(self, other):
        if not isinstance(other, IntervalState):
            return False
        return self.info == other.info

    def deep_copy(self) -> "IntervalState":
        copied_info = {key: value.deep_copy() for key, value in self.info.items()}
        return IntervalState(copied_info)
