from __future__ import annotations

import itertools
from typing import Any, Callable, Generic, Iterable, List, Optional, TypeVar

T = TypeVar("T")


class LINQ(Generic[T], Iterable):
    def __init__(self, native_list: Iterable[T]):
        self._iterable = native_list

    def select(self, function: Callable[[T], Any]):
        return LINQ(function(element) for element in self._iterable)

    def where(self, function: Callable[[T], bool]):
        return LINQ(filter(function, self._iterable))

    def reversed(self):
        return LINQ([i for i in self._iterable][::-1])

    def skip(self, num: int):
        return LINQ(self.to_list()[num:])

    def take(self, num: int):
        return LINQ(self.to_list()[:num])

    def aggregate(self, function: Callable[[Any, T], Any]):
        var = None
        first = True
        for element in self._iterable:
            if first:
                var = element
                first = False
            else:
                var = function(var, element)
        return var

    def all(self, function: Callable[[T], bool]) -> bool:
        for element in self._iterable:
            if not function(element):
                return False
        return True

    def any(self, function: Callable[[T], bool]) -> bool:
        for element in self._iterable:
            if function(element):
                return True
        return False

    def append(self, element: T):
        return LINQ(itertools.chain(self._iterable, [element]))

    def concat(self, linq: "LINQ"[Any]):
        return LINQ(itertools.chain(self._iterable, linq._iterable))

    def contains(self, object: Any) -> bool:
        for element in self._iterable:
            if element == object:
                return True
        return False

    def count(self, function: Optional[Callable[[T], bool]] = None) -> int:
        cnt = 0
        for element in self._iterable:
            if function is None or function(element):
                cnt += 1
        return cnt

    def default_if_empty(self, element: Any):
        return self if not self.empty() else element

    def empty(self) -> bool:
        return self.count() == 0

    def distinct(self):
        lst = []
        for element in self._iterable:
            if element not in lst:
                lst.append(element)
        return LINQ(lst)

    def distinct_by(self, func: Callable[[T, T], bool]):
        lst = []
        for element in self._iterable:
            for compared in lst:
                if func(compared, element):
                    break
            else:
                lst.append(element)
        return LINQ(lst)

    def element_at(self, index: int):
        return self.to_list()[index]

    def element_at_or_default(self, index: int, default: Any):
        lst = self.to_list()
        try:
            return lst[index]
        except IndexError:
            return default

    def difference(self, iterable: Iterable[Any]):
        return LINQ(element for element in self._iterable if element not in iterable)

    def first(self, function: Optional[Callable[[T], bool]] = None):
        if self.empty():
            raise IndexError
        for element in self._iterable:
            if function is None or function(element):
                return element
        raise IndexError

    def first_or_default(
        self,
        function: Optional[Callable[[T], bool]] = None,
        default: Optional[Any] = None,
    ):
        try:
            return self.first(function)
        except IndexError:
            return default

    def intersect(self, iterable: Iterable[Any]):
        distinct = self.distinct().to_list()
        distinct2 = LINQ(iterable).distinct().to_list()
        return LINQ(element for element in distinct if element in distinct2)

    def last(self, function: Optional[Callable[[T], bool]] = None):
        if self.empty():
            return IndexError
        val = None
        found = False
        for element in self._iterable:
            if function is None or function(element):
                val = element
                found = True
        if found:
            return val
        else:
            raise IndexError

    def last_or_default(
        self,
        function: Optional[Callable[[T], bool]] = None,
        default: Optional[Any] = None,
    ):
        try:
            return self.last(function)
        except IndexError:
            return default

    def to_list(self) -> List[T]:
        return [element for element in self._iterable]

    def of_type(self, typ: type):
        return LINQ(element for element in self._iterable if isinstance(element, typ))

    def counted(self):
        lst = {}
        for i in self.distinct():
            lst[i] = lst.get(i, 0) + 1
        return LINQ(lst.items())

    def __iter__(self):
        yield from self._iterable

    def join(self, c: str):
        return self.aggregate(lambda x, y: f"{x}{c}{y}")

    def format(self, fmt: str):
        return self.select(lambda t: fmt % t)
