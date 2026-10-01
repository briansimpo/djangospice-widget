from __future__ import annotations

from django.utils.safestring import SafeString

from .widget import Widget



class WidgetBuilder:
    """
    Builds the final HTML representation of a Widget.

    Rendering is delegated entirely to the Widget/HTMLComponent
    rendering pipeline.
    """

    def __init__(self, widget: Widget) -> None:
        self.widget = widget

    def build(self) -> SafeString:
        """Render the widget into HTML."""
        return self.widget.render(request=self.widget.request)

    def __str__(self) -> str:
        return str(self.build())

    def __html__(self) -> SafeString:
        return self.build()