from __future__ import annotations

from collections.abc import Callable
from functools import wraps
from typing import Any

from .registry import WidgetRegistry
from .widget import Widget


def widget(
    func: Callable[..., Any] | None = None,
    *,
    name: str | None = None,
    title: str = "",
    description: str = "",
    template: str | None = None,
    permission: str | None = None,
    enabled: bool = True,
    lazy: bool = False, 
    refreshable: bool = False, 
    refresh_interval: int = 30, 
    priority: int = 100,
    cache_timeout: int | None = None,
    
) -> Callable[..., Any] | type:
    """
    Transforms a standard function into a registered UI Widget class.

    This decorator dynamically generates a `Widget` subclass based on the 
    provided function and metadata, and automatically registers it with the 
    `WidgetRegistry`.

    It acts smartly based on the function's return type:
    - If it returns a `dict`: It merges the dictionary into `get_context_data`.
    - If it returns a `str`: It maps the string to `get_content` (bypassing templates).
    Returns:
        The dynamically generated Widget subclass, or a decorator function.
    """

    def decorator(target_func: Callable[..., Any]) -> type:
        # Convert snake_case function name to CamelCase (e.g., 'user_stats' -> 'UserStatsWidget')
        camel_name = "".join(word.capitalize() for word in target_func.__name__.split("_"))
        class_name = f"{camel_name}Widget"

        # 1. Dynamically build the inner Meta class based on provided kwargs
        # We filter out None values so that the WidgetOptions dataclass applies its defaults
        meta_attrs = {
            k: v for k, v in {
                "name": name,
                "title": title,
                "description": description,
                "template_name": template,
                "permission": permission,
                "enabled": enabled,
                "lazy": lazy,
                "refreshable": refreshable,
                "refresh_interval": refresh_interval,
                "priority": priority,
                "cache_timeout": cache_timeout,
            }.items() if v is not None
        }
        
        Meta = type("Meta", (), meta_attrs)

        # 2. Construct the subclass of Widget with the Meta class attached
        FunctionWidget = type(class_name, (Widget,), {"Meta": Meta})

        # 3. Create a cached executor to prevent running the function twice 
        # (since it might be checked by both get_content and get_context_data)
        def _execute_func(self_instance: Widget) -> Any:
            if not hasattr(self_instance, "_func_result"):
                self_instance._func_result = target_func(self_instance)
            return self_instance._func_result

        # 4. Wire up the Smart Hooks
        @wraps(target_func)
        def get_content(self: Widget) -> str | dict | None:
            result = _execute_func(self)
            
            # If the user returns a string (like HTML/SafeString), render directly
            if isinstance(result, str):
                return result
                
            return super(FunctionWidget, self).get_content()

        @wraps(target_func)
        def get_context(self: Widget) -> dict[str, Any]:
            context = super(FunctionWidget, self).get_context()
            result = _execute_func(self)
            
            # If the user returns a dict, merge it into standard template context
            if isinstance(result, dict):
                return {**context, **result}
                
            return context

        # Attach the hooks to the newly created class
        FunctionWidget.get_context = get_context

        # 5. Register the newly created class
        WidgetRegistry.register(FunctionWidget)

        return FunctionWidget

    # Allow the decorator to be used with or without parentheses
    if func is not None and callable(func):
        return decorator(func)

    return decorator