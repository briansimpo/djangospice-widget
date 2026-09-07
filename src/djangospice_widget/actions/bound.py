from __future__ import annotations

from dataclasses import dataclass

from djangospice_framework.html.attributes import HTMXAttributes

from .action import Action
from .context import ActionContext


@dataclass(frozen=True, slots=True)
class BoundAction:
    """
    An Action bound to a runtime ActionContext.

    Templates consume this object directly and never need to invoke
    action methods with arguments.
    """

    action: Action
    context: ActionContext

    @property
    def name(self) -> str:
        return self.action.name

    @property
    def label(self) -> str | None:
        return self.action.label

    @property
    def icon(self) -> str | None:
        return self.action.icon

    @property
    def description(self) -> str | None:
        return self.action.description

    @property
    def css_class(self) -> str | None:
        return self.action.css_class

    @property
    def confirm(self) -> str | None:
        return self.action.confirm

    @property
    def enabled(self) -> bool:
        return self.action.enabled(self.context)

    @property
    def htmx(self) -> HTMXAttributes:
        return self.action.htmx(self.context)