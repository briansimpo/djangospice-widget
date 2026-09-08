from __future__ import annotations

from typing import Any, TypeVar

from .identifier import WidgetIdentifier
from .registry import WidgetRegistry


WidgetT = TypeVar("WidgetT")


class WidgetResolver:
    """
    Resolves registered widgets from their application and name.

    The resolver is responsible only for discovery and validation. It does
    not instantiate, configure, or execute widgets.
    """

    @classmethod
    def key(cls, app_name: str, name: str) -> str:
        """
        Build the canonical registry key for a widget.
        """
        return str(WidgetIdentifier(app_name, name))

    @classmethod
    def resolve(cls, app_name: str, name: str, *, expected_type: type[WidgetT] | None = None) -> type[WidgetT]:
        """
        Resolve a registered widget class.

        ``expected_type`` can be supplied when a consumer requires a
        particular widget specialization, for example ``DynamicTable``.
        """
        widget_key = cls.key(app_name, name)

        try:
            widget_cls = WidgetRegistry.get(widget_key)
        except KeyError:
            raise LookupError(
                f"Widget '{widget_key}' is not registered."
            ) from None

        if widget_cls is None:
            raise LookupError(
                f"Widget '{widget_key}' is not registered."
            )

        if expected_type is not None:
            if not issubclass(widget_cls, expected_type):
                raise TypeError(
                    f"Widget '{widget_key}' must inherit from "
                    f"{expected_type.__name__}."
                )

        return widget_cls

    @classmethod
    def instantiate(cls, app_name: str, name: str, *, expected_type: type[WidgetT] | None = None, request: Any = None, **kwargs: Any) -> WidgetT:
        """
        Resolve and instantiate a widget.
        """
        widget_cls = cls.resolve(app_name, name, expected_type=expected_type)

        return widget_cls(
            request=request,
            **kwargs,
        )