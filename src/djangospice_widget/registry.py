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
    Thread-safe, app-aware registry for dynamically discovering and storing widget classes.

    This registry uses an auto-discovery utility to scan the project for
    subclasses of `Widget` inside 'widgets' modules. It utilizes reentrant
    locking (RLock) and double-checked locking patterns to guarantee absolute
    thread safety during lazy initialization, reads, and mutations.

    Widgets are registered using their `widget_key` (formatted as 'app_label.name')
    to prevent name collisions between different Django apps.
    """

    # Maps 'app_label.widget_name' -> Widget Class
    _widgets: dict[str, type[Widget]] = {}
    _initialized: bool = False
    _lock = threading.RLock()

    @classmethod
    def load(cls) -> None:
        """
        Lazily discover and register all available widget classes.

        Uses double-checked locking to ensure the project-wide discovery
        routine runs safely and exactly once.
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
    def register(cls, widget: type[Widget]) -> None:
        """
        Register an app-aware widget class in the internal registry mapping.

        Args:
            widget: The widget class subclassing `Widget`.

        Raises:
            ImproperlyConfigured: If a widget with the same app_label and name 
                is already registered.
        """
        # Resolve the unique registration key (e.g., 'auth.recent_users')
        # fallback to using .name if .widget_key is not built yet (safeguard)
        reg_key = getattr(widget, "widget_key", widget.name)

        with cls._lock:
            if reg_key in cls._widgets:
                existing_widget = cls._widgets[reg_key]
                raise ImproperlyConfigured(
                    f"Widget '{widget.name}' in app '{getattr(widget, 'app_label', 'unknown')}' "
                    f"is already registered by class `{existing_widget.__module__}.{existing_widget.__name__}`. "
                    f"Conflicting class: `{widget.__module__}.{widget.__name__}`."
                )

            cls._widgets[reg_key] = widget

        logger.debug(
            "Registered widget '%s' (%s).",
            reg_key,
            widget.__module__,
        )

    @classmethod
    def unregister(cls, widget_key: str) -> None:
        """
        Remove a widget class from the registry by its registration key.

        Args:
            widget_key: The namespaced identifier (e.g., 'myapp.my_widget').
        """
        cls.load()
        with cls._lock:
            cls._widgets.pop(widget_key, None)

    @classmethod
    def get(cls, widget_key: str) -> type[Widget] | None:
        """
        Retrieve a widget class by its registration key.

        Args:
            widget_key: The namespaced identifier (e.g., 'myapp.my_widget').

        Returns:
            The matching widget class, or None if not found.
        """
        cls.load()
        return cls._widgets.get(widget_key)

    @classmethod
    def widgets(cls) -> dict[str, type[Widget]]:
        """
        Retrieve a shallow copy of all registered widget classes.

        Returns:
            A dictionary mapping namespaced registration keys to their respective classes.
        """
        cls.load()
        with cls._lock:
            return cls._widgets.copy()

    @classmethod
    def keys(cls) -> tuple[str, ...]:
        """
        Retrieve the unique registration keys of all currently registered widgets.

        Returns:
            A tuple containing all registration keys (e.g., 'myapp.my_widget').
        """
        cls.load()
        with cls._lock:
            return tuple(cls._widgets)

    # Alias for backwards compatibility of registry naming lists
    names = keys

    @classmethod
    def values(cls) -> tuple[type[Widget], ...]:
        """
        Retrieve all currently registered widget classes.

        Returns:
            A tuple containing all registered Widget subclasses.
        """
        cls.load()
        with cls._lock:
            return tuple(cls._widgets.values())

    @classmethod
    def clear(cls) -> None:
        """
        Clear the registry state and reset initialization flags.

        Primarily intended to ensure test isolation across environments where 
        mocking or dynamic widget definitions are leveraged.
        """
        with cls._lock:
            cls._widgets.clear()
            cls._initialized = False

    @classmethod       
    def exists(cls, widget_key: str) -> bool:
        """
        Check if a widget is currently registered by its registration key.

        Args:
            widget_key: The namespaced identifier (e.g., 'myapp.my_widget').
            
        Returns:
            True if the widget is registered, False otherwise.
        """
        return cls.get(widget_key) is not None

    @classmethod
    def groups(cls) -> dict[str | None, list[type[Widget]]]:
        """
        Group all registered widgets by their configured group name.

        Returns:
            A dictionary mapping group names to lists of widget classes.
            Widgets without a specified group will fall under the `None` key.
        """
        groups: dict[str | None, list[type[Widget]]] = {}

        for widget in cls.values():
            # Widget classes still contain groups
            groups.setdefault(widget.group, []).append(widget)

        return groups

    @classmethod
    def __iter__(cls) -> Iterator[type[Widget]]:
        """
        Iterate over all registered widget classes.
        """
        return iter(cls.values())

    @classmethod
    def __len__(cls) -> int:
        """
        Get the total number of registered widgets.
        """
        cls.load()
        with cls._lock:
            return len(cls._widgets)