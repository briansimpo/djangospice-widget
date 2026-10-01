from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from django.http import HttpRequest

if TYPE_CHECKING:
    from djangospice_widget.widget import Widget


@dataclass(slots=True)
class ActionContext:
    """
    Runtime context supplied to an Action.
    """

    widget: "Widget"

    request: HttpRequest

    object: Any | None = None

    objects: tuple[Any, ...] = ()

    data: dict[str, Any] = field(default_factory=dict)

    @property
    def user(self):
        return self.request.user

    @property
    def is_single(self) -> bool:
        return self.object is not None

    @property
    def is_bulk(self) -> bool:
        return bool(self.objects)

    @property
    def count(self) -> int:
        return len(self.objects)