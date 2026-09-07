from __future__ import annotations

from typing import ClassVar

from django.http import HttpRequest
from djangospice_framework.response.response import Response

from .dispatchers import ActionDispatcher, BaseDispatcher, MethodDispatcher
from .exceptions import DispatcherNotFound
from .widget import Widget


class WidgetExecutor:
    """
    Orchestrates the lifecycle, authorization, and dispatching pipeline 
    for an incoming widget request.
    """

    dispatchers: ClassVar[tuple[type[BaseDispatcher], ...]] = (
        ActionDispatcher,
        MethodDispatcher,
    )

    def __init__(self, widget: Widget, request: HttpRequest) -> None:
        self.widget = widget
        self.request = request
        self.widget.request = request

    def execute(self) -> Response:
        """Run the full lifecycle pipeline and dispatch the request."""
        self.widget.initialize()
        self.widget.configure()
        self.widget.configure_htmx()
        self.widget.authorize()

        return self.dispatch()

    def dispatch(self) -> Response:
        """Iterate through registered dispatchers and invoke the first match."""
        for dispatcher_cls in self.dispatchers:
            dispatcher = dispatcher_cls(self.widget, self.request)

            if dispatcher.can_dispatch():
                return dispatcher.dispatch()

        raise DispatcherNotFound("No valid dispatcher found for this request.")