import re


def slugify(class_name: str) -> str:

    
    """
    Convert CamelCase class names to snake_case, stripping the 'Widget' suffix.
    """
    name = class_name
    if name.endswith("Widget"):
        name = name[:-6]  # Removes 'Widget' suffix

    # Convert CamelCase to snake_case
    name = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub("([a-z0-9])([A-Z])", r"\1_\2", name).lower()


def widget_class_name(func_name: str) -> str:
    """
    Convert a widget function name to its generated class name.

    Examples:
        hello                -> HelloWidget
        hello_widget         -> HelloWidget
        student_stats        -> StudentStatsWidget
        student_stats_widget -> StudentStatsWidget
    """

    _WIDGET_SUFFIX = "Widget"


    name = str(func_name).strip()

    # Remove any existing Widget suffix.
    while name.lower().endswith(_WIDGET_SUFFIX.lower()):
        name = name[: -len(_WIDGET_SUFFIX)]

    parts = [
        part
        for part in name.split("_")
        if part
    ]

    class_name = "".join(
        part[:1].upper() + part[1:]
        for part in parts
    )

    return f"{class_name}{_WIDGET_SUFFIX}"