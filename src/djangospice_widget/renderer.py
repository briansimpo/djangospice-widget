from __future__ import annotations

from django.utils.safestring import SafeString

from .builder import WidgetBuilder
from .cache import WidgetCache
from .exceptions import WidgetNotVisible
from .widget import Widget
from .placeholder import Placeholder


class WidgetRenderer:
    """
    Executes the rendering lifecycle for a widget.
    """

    def __init__(self, widget: Widget) -> None:
        self.widget = widget

    def render(self) -> SafeString:
        self.check_visibility()

        if self.should_render_placeholder():
            return self.render_placeholder()

        cached = self.get_cached()
        if cached is not None:
            return cached

        content = self.build()

        self.cache(content)

        return content

    def check_visibility(self) -> None:
        if not self.widget.visible():
            raise WidgetNotVisible(
                f"Widget '{self.widget.widget_key}' is not visible."
            )

    def should_render_placeholder(self) -> bool:
        return (
            self.widget.lazy
            and not self.widget.is_lazy_fetch
        )

    def render_placeholder(self) -> SafeString:
        placeholder = Placeholder(
            request=self.widget.request,
            target_id=self.widget.id,
            target_url=self.widget.endpoint,
            target_title=self.widget.title,
        )

        return WidgetRenderer(placeholder).render()

    def build(self) -> SafeString:
        return WidgetBuilder(self.widget).build()

    def get_cached(self) -> SafeString | None:
        if not self.widget.should_cache():
            return None

        return WidgetCache.get(self.widget)

    def cache(self, content: SafeString) -> None:
        if self.widget.should_cache():
            WidgetCache.set(self.widget, content)

    def invalidate_cache(self) -> None:
        WidgetCache.delete(self.widget)