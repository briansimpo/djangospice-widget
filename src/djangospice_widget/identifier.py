from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class WidgetIdentifier:

    app_name: str
    widget_name: str

    def __post_init__(self) -> None:
        app_name = self.app_name.strip().casefold()
        widget_name = self.widget_name.strip().casefold()

        if not app_name:
            raise ValueError("Widget app_name cannot be empty.")

        if not widget_name:
            raise ValueError("Widget widget_name cannot be empty.")

        object.__setattr__(self, "app_name", app_name)
        object.__setattr__(self, "widget_name", widget_name)

    @property
    def key(self) -> tuple[str, str]:
        return self.app_name, self.widget_name
    
    def __str__(self) -> str:
        return f"{self.app_name}.{self.widget_name}"

    @classmethod
    def from_model(cls, model) -> "WidgetIdentifier":
        return cls(
            app_name=model._meta.app_label,
            widget_name=model._meta.model_name,
        )