from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class PaginationConfig:
    """
    Resolved pagination configuration.

    Represents what pagination should look like for the current request.
    It does not describe the actual result set.
    """

    enabled: bool
    page: int
    page_size: int
    page_size_options: tuple[int, ...]

    page_parameter: str
    page_size_parameter: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class PaginationState:
    """
    Resolved pagination state for an actual result set.

    This is independent of the underlying pagination implementation.
    """

    page: int
    page_size: int
    total: int
    pages: int

    has_next: bool
    has_previous: bool

    next_page: int | None = None
    previous_page: int | None = None

    first_page: int | None = None
    last_page: int | None = None

    page_size_options: tuple[int, ...] = ()

    page_parameter: str = "page"
    page_size_parameter: str = "page_size"

    @property
    def is_first(self) -> bool:
        return not self.has_previous

    @property
    def is_last(self) -> bool:
        return not self.has_next

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)