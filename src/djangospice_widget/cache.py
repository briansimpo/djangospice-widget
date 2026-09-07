from __future__ import annotations

from hashlib import sha256
from typing import Any

from django.core.cache import cache
from django.utils.safestring import SafeString

from .builder import WidgetBuilder
from .widget import Widget


class WidgetCache:
    """
    Manager for caching and retrieving widget response.

    This class provides a clean interface over Django's caching framework
    to store, retrieve, and invalidate serialized widget states based on
    their unique cache digests.
    """

    PREFIX = "widget"

    @classmethod
    def cache_digest(cls, widget: Widget) -> str:
        """
        Generate a predictable, hashed string based on the cache key.

        Args:
            widget: The widget instance to generate the digest for.

        Returns:
            A SHA256 hex digest representing the unique cache state.
        """
        # Widget.cache_key() now returns a formatted string
        key_str = widget.cache_key()
        return sha256(key_str.encode("utf-8")).hexdigest()

    @classmethod
    def key(cls, widget: Widget) -> str:
        """
        Generate the full cache key for a given widget.

        Args:
            widget: The widget instance.

        Returns:
            A string combining the prefix and the widget's unique digest.
        """
        return f"{cls.PREFIX}:{cls.cache_digest(widget)}"

    @classmethod
    def get(cls, widget: Widget) -> Any | None:
        """
        Retrieve a widget's cached response, if available.

        Args:
            widget: The widget instance to look up.

        Returns:
            The cached response/content, or None if the widget should 
            not be cached or the cache entry is missing/expired.
        """
        if not widget.should_cache():
            return None
        return cache.get(cls.key(widget))

    @classmethod
    def set(cls, widget: Widget, value: Any) -> Any:
        """
        Store a widget's rendered output in the cache.

        Args:
            widget: The widget instance being cached.
            value: The rendered content to store.

        Returns:
            The passed-in value, allowing for convenient inline returns.
        """
        if not widget.should_cache():
            return value

        cache.set(
            cls.key(widget),
            value,
            widget.cache_timeout,
        )
        return value

    @classmethod
    def delete(cls, widget: Widget) -> None:
        """
        Remove a specific widget's response from the cache.

        Args:
            widget: The widget instance to remove.
        """
        cache.delete(cls.key(widget))

    @classmethod
    def exists(cls, widget: Widget) -> bool:
        """
        Check if a valid cached response exists for the widget.
        Uses `has_key` to avoid pulling large HTML payloads into memory.

        Args:
            widget: The widget instance to check.

        Returns:
            True if a cached response exists, False otherwise.
        """
        if not widget.should_cache():
            return False
            
        return cache.has_key(cls.key(widget))

    @classmethod
    def refresh(cls, widget: Widget) -> None:
        """
        Invalidate the cache for a specific widget.

        Args:
            widget: The widget instance to refresh.
        """
        cls.delete(widget)

    @classmethod
    def clear(cls) -> None:
        """
        Clear the entire Django cache.
        
        Warning: This invokes `cache.clear()`, which flushes the entire 
        global cache backend, not just the keys managed by WidgetCache.
        """
        cache.clear()

    @classmethod
    def get_or_set(cls, widget: Widget) -> SafeString | Any:
        """
        Retrieve the cached widget content, or render and cache it if missing.

        Leverages Django's native `cache.get_or_set` with a callable to ensure
        the widget is only built if a cache miss occurs.

        Args:
            widget: The widget instance to process.

        Returns:
            The cached or newly rendered widget HTML content.
        """
        if not widget.should_cache():
            return WidgetBuilder(widget).build()

        return cache.get_or_set(
            cls.key(widget),
            lambda: WidgetBuilder(widget).build(),
            widget.cache_timeout,
        )