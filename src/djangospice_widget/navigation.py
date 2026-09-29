from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .interaction import Interaction


@dataclass(frozen=True, slots=True)
class Navigation:

    widget: Any

    def page(self, number: int) -> Interaction:
        return self.widget.interaction(
            url=self.widget.url(page=number),
            target=self.widget.htmx_target,
        )