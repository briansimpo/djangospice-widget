from __future__ import annotations

from typing import Any

from django.http import Http404, HttpRequest, HttpResponse
from django.views import View
from djangospice_framework.response.shortcuts import render_response

from .exceptions import WidgetNotVisible
from .executor import WidgetExecutor
from .identifier import WidgetIdentifier
from .registry import WidgetRegistry


class WidgetView(View):
    """
    HTTP view endpoint for dynamically resolving, configuring, and executing widgets.

    Maps routing parameters (`app_name`, `name`) to a registered Widget, instantiates 
    it with request query state and path variables, and delegates execution 
    to the WidgetExecutor.
    """

    def dispatch(self, request: HttpRequest, app_name: str, name: str, *args: Any, **kwargs: Any) -> HttpResponse:
        widget_key = str(WidgetIdentifier(app_name, name))

        try:
            widget_cls = WidgetRegistry.get(widget_key)
        except KeyError:
            raise Http404(f"Widget '{widget_key}' not found.")

        if widget_cls is None:
            raise Http404(f"Widget '{widget_key}' not found.")

        # Merge URL kwargs with GET query parameters for widget initialization
        widget_kwargs = {**request.GET.dict(), **kwargs}

        widget = widget_cls(
            request=request,
            **widget_kwargs,
        )

        try:
            response = WidgetExecutor(widget, request).execute()
        except WidgetNotVisible:
            raise Http404(f"Widget '{widget_key}' is not accessible.")

        return render_response(response, request)