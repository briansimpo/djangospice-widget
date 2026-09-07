from __future__ import annotations

from typing import Any

from django import template
from django.utils.safestring import SafeString, mark_safe

from djangospice_widget.exceptions import WidgetNotVisible
from djangospice_widget.registry import WidgetRegistry
from djangospice_widget.utils import render
from djangospice_widget.widget import Widget


register = template.Library()


@register.simple_tag(takes_context=True)
def render_widget(context: template.Context, widget_key: str, **kwargs: Any) -> SafeString:
    """
    Template tag to dynamically render a registered widget.
    
    Usage:
        {% render_widget "analytics:monthly_chart" period="year" %}
    """
    request = context.get("request")

    try:
        widget_class = WidgetRegistry.get(widget_key)
    except KeyError:
        return mark_safe("")

    widget = widget_class(request=request, **kwargs)

    try:
       return render(widget)
    except WidgetNotVisible:
        return mark_safe("")


@register.simple_tag(takes_context=True)
def render_children(context: template.Context, widget: Widget) -> SafeString:
    """
    Render all direct children of a widget.

    Example:

        {% render_children widget %}
    """
    rendered = []

    for child in widget.get_children():
        rendered.append(render(child))

    return mark_safe("".join(rendered))

@register.simple_tag(takes_context=True)
def render_slot(context: template.Context, widget: Widget, name: str) -> SafeString:
    """
    Render all widgets assigned to a named slot.

    Example:

        {% render_slot widget "header" %}
    """
    rendered = []

    for child in widget.get_slot(name):
        rendered.append(render(child))

    return mark_safe("".join(rendered))

