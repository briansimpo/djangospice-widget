from __future__ import annotations

from functools import cached_property

from djangospice_framework.core.collection import ObjectCollection

from .action import Action


class Actions(ObjectCollection[Action]):
    """
    Immutable collection of widget actions.

    Provides fast lookup by name and efficient grouping for rendering.
    """

    @cached_property
    def _map(self) -> dict[str, Action]:
        return {
            action.name: action
            for action in self._items
        }

    # ------------------------------------------------------------------
    # Access
    # ------------------------------------------------------------------

    def get(self, name: str) -> Action | None:
        return self._map.get(name)

    def require(self, name: str) -> Action:
        try:
            return self._map[name]
        except KeyError:
            raise KeyError(
                f"Unknown action '{name}'"
            ) from None
