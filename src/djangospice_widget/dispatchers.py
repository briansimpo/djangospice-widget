from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from django.http import HttpRequest
from djangospice_framework.response.response import Response

from .actions import ActionContext

if TYPE_CHECKING:
    from .widget import Widget


class BaseDispatcher(ABC):
    """Abstract base class for widget dispatchers."""

    def __init__(self, widget: Widget, request: HttpRequest) -> None:
        self.widget = widget
        self.request = request

    @abstractmethod
    def can_dispatch(self) -> bool:
        """Determine whether this dispatcher can handle the incoming request."""
        pass

    @abstractmethod
    def dispatch(self) -> Response:
        """Execute the dispatch logic and return a framework Response."""
        pass


class ActionDispatcher(BaseDispatcher):
    """Dispatches custom actions declared on the widget."""

    parameter: str = "action"

    def can_dispatch(self) -> bool:
        """Check if an action key is present in request GET or POST data."""
        data = self.widget.request_data
        return bool(data and self.parameter in data)

    def dispatch(self) -> Response:
        """Locate and execute the requested action with full context."""
        name = self.widget.request_value(self.parameter)
        actions = self.widget.get_action_collection()
        action = actions.require(name)

        context = ActionContext(
            widget=self.widget,
            request=self.request,
            object=self.widget.get_object(),
            objects=self.widget.get_objects(),
            data=self.widget.get_data(),
        )

        return action.dispatch(context)


class MethodDispatcher(BaseDispatcher):
    """Fallback dispatcher that maps request HTTP methods directly to widget handlers."""

    def can_dispatch(self) -> bool:
        return True

    def dispatch(self) -> Response:
        handler = getattr(self.widget, self.request.method.lower(), None)

        if handler is None or not callable(handler):
            return self.widget.method_not_allowed()

        return handler()