from __future__ import annotations

from .registry import WidgetRegistry
from .widget import Widget


def widget(cls: type[Widget]) -> type[Widget]:
    """
    Register a Widget class explicitly.
    """
    WidgetRegistry.register(cls)
    return cls