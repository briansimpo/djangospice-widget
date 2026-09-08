from __future__ import annotations

from typing import Any

import django_filters
from django.db.models import QuerySet


class FilterComposer:
    """
    Integrates a django-filter FilterSet into a queryset pipeline.
    """

    def __init__(
        self,
        *,
        request=None,
        filterset_class: type[django_filters.FilterSet] | None = None,
       
    ) -> None:
        self.request = request
        self.filterset_class = filterset_class
        self.filterset: django_filters.FilterSet | None = None

    def compose(
        self,
        queryset: QuerySet[Any],
    ) -> django_filters.FilterSet | None:
        if self.filterset_class is None:
            self.filterset = None
            return None

        self.filterset = self.filterset_class(
            data=self.request.GET if self.request else None,
            queryset=queryset,
            request=self.request,
        )

        return self.filterset

    def apply(self, queryset: QuerySet[Any]) -> QuerySet[Any]:
        filterset = self.compose(queryset)

        if filterset is None:
            return queryset

        return filterset.qs