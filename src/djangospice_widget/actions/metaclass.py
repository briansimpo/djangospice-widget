from __future__ import annotations

from django.utils.text import camel_case_to_spaces, slugify


class ActionMetaclass(type):
    """
    Metaclass for Action.

    Normalizes declarative action attributes during class creation.
    """

    def __new__(mcls, name: str, bases: tuple[type, ...], attrs: dict) -> type:

        cls = super().__new__(mcls, name, bases, attrs)

        # Skip the abstract base Action.
        if not bases or name == "Action":
            return cls

        class_name = name

        # Strip the "Action" suffix.
        if class_name.endswith("Action"):
            class_name = class_name[:-6]

        # ------------------------------------------------------------------
        # Identity
        # ------------------------------------------------------------------

        if getattr(cls, "name", None) is None:
            cls.name = (
                slugify(
                    camel_case_to_spaces(class_name)
                )
                .replace("-", "_")
            )

        if not cls.name:
            raise TypeError(
                f"{cls.__name__} has an invalid action name."
            )

        if getattr(cls, "label", None) is None:
            cls.label = camel_case_to_spaces(
                class_name
            ).title()

        # ------------------------------------------------------------------
        # Presentation
        # ------------------------------------------------------------------

        cls.order = int(getattr(cls, "order", 100))

        # ------------------------------------------------------------------
        # Behaviour
        # ------------------------------------------------------------------

        cls.method = str(
            getattr(cls, "method", "POST")
        ).upper()

        return cls