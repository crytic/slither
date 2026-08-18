import abc

from slither.core.source_mapping.source_mapping import SourceMapping


class Type(SourceMapping, metaclass=abc.ABCMeta):
    @property
    @abc.abstractmethod
    def storage_size(self) -> tuple[int, bool]:
        """
        Computes and returns storage layout related metadata

        :return: (int, bool) - the number of bytes this type will require, and whether it must start in
        a new slot regardless of whether the current slot can still fit it
        """

    @property
    @abc.abstractmethod
    def is_dynamic(self) -> bool:
        """True if the size of the type is dynamic"""
