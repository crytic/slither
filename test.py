import abc
from typing import Union


class S:
    pass


class S1(S):
    pass


class A(abc.ABC):
    @property
    @abc.abstractmethod
    def test(self) -> Union[Union[int, Union[Union[S, S1, str]]]]:
        return 0


class B(A):
    @property
    def test(self) -> Union[str, S1]:
        return "t"
