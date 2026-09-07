from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlencode
from typing import Any


@dataclass(frozen=True, slots=True)
class QueryState:
    values: tuple[tuple[str, tuple[str, ...]], ...] = ()

    @classmethod
    def from_querydict(cls, querydict: Any) -> "QueryState":
        return cls(
            tuple(
                (key, tuple(values))
                for key, values in querydict.lists()
            )
        )

    def set(self, name: str, value: object | None) -> "QueryState":
        data = dict(self.values)

        if value is None or value == "":
            data.pop(name, None)
        else:
            data[name] = (str(value),)

        return QueryState(tuple(data.items()))

    def remove(self, *names: str) -> "QueryState":
        return QueryState(
            tuple(
                (key, values)
                for key, values in self.values
                if key not in names
            )
        )

    def encode(self) -> str:
        return urlencode(
            [
                (key, value)
                for key, values in self.values
                for value in values
            ]
        )