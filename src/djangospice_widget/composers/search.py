from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from django.db.models import Q, QuerySet


class SearchComposer:
    """
    Applies OR-based icontains search across configured fields.
    """

    def __init__(
        self,
        *,
        request=None,
        fields: Iterable[str] = (),
        parameter: str = "q",
    ) -> None:
        self.request = request
        self.fields = tuple(fields)
        self.parameter = parameter

    def get_term(self) -> str:
        if self.request is None:
            return ""

        return self.request.GET.get(self.parameter, "").strip()

    def apply(self, queryset: QuerySet[Any]) -> QuerySet[Any]:
        term = self.get_term()

        if not term or not self.fields:
            return queryset

        query = Q()

        for field in self.fields:
            query |= Q(**{f"{field}__icontains": term})

        return queryset.filter(query)