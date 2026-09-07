from __future__ import annotations


class WidgetError(Exception):
    """
    Base exception for the widget framework.
    """


class WidgetNotFound(WidgetError):
    def __init__(self, widget: str) -> None:
        self.widget = widget
        super().__init__(f"Widget '{widget}' is not registered.")
        

class WidgetNotVisible(WidgetError):
    def __init__(self, widget: str) -> None:
        self.widget = widget
        super().__init__(f"Widget '{widget}' is not visible.")


class DispatcherNotFound(WidgetError):
    def __init__(self, widget: str) -> None:
        self.widget = widget
        super().__init__(f"Widget Dispatcher not found.")

