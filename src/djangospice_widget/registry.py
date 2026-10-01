from __future__ import annotations

import logging
import threading
from collections.abc import Iterator

from django.core.exceptions import ImproperlyConfigured

from djangospice_framework.apps.discovery import ModuleDiscovery

from .widget import Widget

logger = logging.getLogger(__name__)



class WidgetRegistry:
    """
    Thread-safe, app-aware registry for Widget classes.

    Widgets are identified by their namespaced key:

        app_label.widget_name

    Registration is idempotent for the same class. This allows widgets to
    be registered explicitly with ``@widget`` while also being discovered
    automatically by ``ModuleDiscovery``.
    """

    _widgets: dict[str, type[Widget]] = {}
    _initialized: bool = False
    _lock = threading.RLock()

    @classmethod
    def _get_key(cls, widget: type[Widget]) -> str:
        """
        Resolve the registry key for a Widget class.
        """
        return f"{widget.app_label}.{widget.name}"

    @classmethod
    def load(cls) -> None:
        """
        Lazily discover and register all available Widget classes.
        """
        if cls._initialized:
            return

        with cls._lock:
            if cls._initialized:
                return

            ModuleDiscovery.discover(
                module="widgets",
                base_class=Widget,
                callback=cls.register,
            )

            cls._initialized = True

    @classmethod
    def register(cls, widget: type[Widget]) -> type[Widget]:
        """
        Register a Widget class.

        Registration is idempotent when the exact same class has already
        been registered.

        A conflict is raised only when another class attempts to use the
        same ``app_label.name`` identity.
        """
        if not isinstance(widget, type):
            raise TypeError(
                "WidgetRegistry.register() expects a Widget class."
            )

        if not issubclass(widget, Widget):
            raise TypeError(
                f"{widget.__module__}.{widget.__qualname__} "
                "is not a Widget subclass."
            )

        if not widget.name:
            raise ImproperlyConfigured(
                f"Widget {widget.__module__}.{widget.__qualname__} "
                "must define a name."
            )

        if not widget.app_label:
            raise ImproperlyConfigured(
                f"Widget {widget.__module__}.{widget.__qualname__} "
                "must define an app_label."
            )

        reg_key = cls._get_key(widget)

        with cls._lock:
            existing_widget = cls._widgets.get(reg_key)

            # ----------------------------------------------------------
            # Already registered with the exact same class.
            #
            # This is expected when:
            #
            #     @widget
            #     class HelloWidget(Widget):
            #         ...
            #
            # is later found again by ModuleDiscovery.
            # ----------------------------------------------------------
            if existing_widget is widget:
                return widget

            # ----------------------------------------------------------
            # Same identity, different class.
            # ----------------------------------------------------------
            if existing_widget is not None:
                raise ImproperlyConfigured(
                    f"Widget '{widget.name}' in app "
                    f"'{widget.app_label}' is already registered by "
                    f"class "
                    f"`{existing_widget.__module__}."
                    f"{existing_widget.__qualname__}`. "
                    f"Conflicting class: "
                    f"`{widget.__module__}.{widget.__qualname__}`."
                )

            cls._widgets[reg_key] = widget

        logger.debug(
            "Registered widget '%s' (%s).",
            reg_key,
            f"{widget.__module__}.{widget.__qualname__}",
        )

        return widget

    @classmethod
    def unregister(cls, widget_key: str) -> None:
        """
        Remove a Widget by its namespaced key.
        """
        with cls._lock:
            cls._widgets.pop(widget_key, None)

    @classmethod
    def get(cls, widget_key: str) -> type[Widget] | None:
        """
        Retrieve a Widget by its namespaced key.
        """
        cls.load()

        with cls._lock:
            return cls._widgets.get(widget_key)

    @classmethod
    def widgets(cls) -> dict[str, type[Widget]]:
        """
        Return a shallow copy of all registered Widgets.
        """
        cls.load()

        with cls._lock:
            return cls._widgets.copy()

    @classmethod
    def keys(cls) -> tuple[str, ...]:
        """
        Return all registered Widget keys.
        """
        cls.load()

        with cls._lock:
            return tuple(cls._widgets)

    names = keys

    @classmethod
    def values(cls) -> tuple[type[Widget], ...]:
        """
        Return all registered Widget classes.
        """
        cls.load()

        with cls._lock:
            return tuple(cls._widgets.values())

    @classmethod
    def clear(cls) -> None:
        """
        Clear the registry.

        Primarily useful for tests and development environments.
        """
        with cls._lock:
            cls._widgets.clear()
            cls._initialized = False

    @classmethod
    def exists(cls, widget_key: str) -> bool:
        """
        Check whether a Widget is registered.
        """
        cls.load()

        with cls._lock:
            return widget_key in cls._widgets

    @classmethod
    def groups(cls) -> dict[str | None, list[type[Widget]]]:
        """
        Group registered Widgets by their group.
        """
        groups: dict[str | None, list[type[Widget]]] = {}

        for widget in cls.values():
            groups.setdefault(widget.group, []).append(widget)

        return groups

    @classmethod
    def __iter__(cls) -> Iterator[type[Widget]]:
        return iter(cls.values())

    @classmethod
    def __len__(cls) -> int:
        return len(cls.values())