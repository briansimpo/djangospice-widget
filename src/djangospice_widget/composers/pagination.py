from __future__ import annotations

from collections.abc import Iterable

from ..pagination import PaginationConfig


class PaginationComposer:
    """
    Resolves pagination configuration from the request.

    This class does not paginate records and does not know the
    resulting number of records/pages.
    """

    def __init__(
        self,
        *,
        request=None,
        paginate: bool = True,
        default_size: int = 20,
        size_options: Iterable[int] = (10, 20, 50, 100),
        max_size: int = 100,
        page_parameter: str = "page",
        size_parameter: str = "page_size",
    ) -> None:
        self.request = request
        self.paginate = paginate
        self.default_size = default_size
        self.size_options = tuple(size_options)
        self.max_size = max_size
        self.page_parameter = page_parameter
        self.size_parameter = size_parameter

    def get_size_options(self) -> tuple[int, ...]:
        return tuple(
            size
            for size in self.size_options
            if size <= self.max_size
        )

    def get_size(self) -> int:
        if not self.paginate:
            return self.default_size

        if self.request is None:
            return self.default_size

        value = self.request.GET.get(self.size_parameter)

        if not value:
            return self.default_size

        try:
            size = int(value)
        except (TypeError, ValueError):
            return self.default_size

        if size not in self.get_size_options():
            return self.default_size

        return size

    def get_page(self) -> int:
        if not self.paginate or self.request is None:
            return 1

        value = self.request.GET.get(self.page_parameter)

        if not value:
            return 1

        try:
            page = int(value)
        except (TypeError, ValueError):
            return 1

        return max(page, 1)

    def compose(self) -> PaginationConfig:
        return PaginationConfig(
            enabled=self.paginate,
            page=self.get_page(),
            page_size=self.get_size(),
            page_size_options=self.get_size_options(),
            page_parameter=self.page_parameter,
            page_size_parameter=self.size_parameter,
        )