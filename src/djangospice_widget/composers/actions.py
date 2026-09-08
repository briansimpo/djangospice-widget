from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from djangospice_widget.actions import ActionContext, Actions, BoundAction
from djangospice_widget.widget import Widget


class ActionComposer:
    """
    Resolves and binds actions against a widget/request context.

    The composer is generic and does not know whether actions belong
    to a table, form, list, dashboard, or another widget.
    """

    def __init__(
        self,
        *,
        widget: Widget,
        request=None,
        actions: Actions = (),
        data: Any = None,
        object: Any = None,
        objects: Iterable[Any] = (),
    ) -> None:
        self.widget = widget
        self.request = request
        self.actions = actions
        self.data = data
        self.object = object
        self.objects = tuple(objects)

    def context(self) -> ActionContext:
        return ActionContext(
            widget=self.widget,
            request=self.request,
            object=self.object,
            objects=self.objects,
            data=self.data,
        )

    def compose(self) -> tuple[BoundAction, ...]:
        context = self.context()

        return tuple(
            self.widget.bind_action(action, context)
            for action in self.actions
            if action.visible(context)
        )