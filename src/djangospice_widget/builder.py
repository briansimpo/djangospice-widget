from __future__ import annotations

from typing import Any

from django.template.loader import render_to_string
from django.utils.safestring import SafeString, mark_safe

from .exceptions import WidgetError
from .widget import Widget


class WidgetBuilder:
    """
    Builds the HTML representation of a widget.
    """

    def __init__(self, widget: Widget) -> None:
        self.widget = widget

    def build(self) -> SafeString:
        content = self.widget.get_content()

        if isinstance(content, str):
            rendered = mark_safe(content)
        else:
            context = self.widget.get_context()

            if isinstance(content, dict):
                context.update(content)

            rendered = self.content(context)

        return rendered

    def content(self, context: dict[str, Any]) -> SafeString:
        try:
            template = self.widget.get_template()
        except ValueError as exc:
            raise WidgetError(str(exc)) from exc

        if not template:
            raise WidgetError(
                f"Widget '{self.widget.name}' "
                f"({self.widget.__class__.__name__}) "
                "does not define a template."
            )

        return mark_safe(
            render_to_string(
                template_name=template,
                context=context,
                request=self.widget.request,
            )
        )
