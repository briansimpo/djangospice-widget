from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class WidgetIdentifier:

    app_name: str
    name: str

    def __post_init__(self) -> None:
        app_name = self.app_name.strip().casefold()
        name = self.name.strip().casefold()

        if not app_name:
            raise ValueError("Lookup app name cannot be empty.")

        if not name:
            raise ValueError("Lookup name cannot be empty.")

        object.__setattr__(self, "app_name", app_name)
        object.__setattr__(self, "name", name)

    @property
    def key(self) -> tuple[str, str]:
        return self.app_name, self.name
    
    def __str__(self) -> str:
        return f"{self.app_name}.{self.name}"

    @classmethod
    def from_model(cls, model) -> "WidgetIdentifier":
        return cls(
            app_name=model._meta.app_label,
            name=model._meta.model_name,
        )