from __future__ import annotations

from typing import Any

from django.http import Http404, HttpRequest, HttpResponse
from django.views import View
from djangospice_framework.response.shortcuts import render_response

from .exceptions import WidgetNotVisible
from .executor import WidgetExecutor
from .resolver import WidgetResolver


class WidgetView(View):
    """
    HTTP view endpoint for dynamically resolving, configuring, and executing widgets.

    Maps routing parameters (`app_name`, `name`) to a registered Widget, instantiates 
    it with request query state and path variables, and delegates execution 
    to the WidgetExecutor.
    """

    def dispatch(self, request: HttpRequest, app_name: str, name: str, *args: Any, **kwargs: Any) -> HttpResponse:
        try:
            widget_cls = WidgetResolver.resolve(
                app_name,
                name,
            )
        except LookupError as exc:
            raise Http404(str(exc)) from exc

        widget_kwargs = {
            **request.GET.dict(),
            **kwargs,
        }

        widget = widget_cls(
            request=request,
            **widget_kwargs,
        )

        try:
            response = WidgetExecutor(widget, request).execute()
        except WidgetNotVisible:
            raise Http404(
                f"Widget '{app_name}:{name}' is not accessible."
            ) from None
        return render_response(response, request)