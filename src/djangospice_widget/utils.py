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

