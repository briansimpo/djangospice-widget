from typing import Any
from .apps import namespace
from .widget import Widget


class Placeholder(Widget):
    
    """System level specialized element creating DOM skeleton attachment points."""
    
    class Meta:
        name = "djangospice_widget_placeholder"
        template_name = f"{namespace}/placeholder.html"
        lazy = False
        cache_timeout = None


    def get_context(self) -> dict[str, Any]:
        return super().get_context() | {
            "target_id": self.kwargs.get("target_id"),
            "target_url": self.kwargs.get("target_url"),
            "target_title": self.kwargs.get("target_title"),
        }