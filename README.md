# djangospice-widget

Reusable, composable, request-aware UI widgets for Django.

`djangospice-widget` provides a declarative widget system for building server-rendered Django interfaces from small, reusable UI units. Widgets can render templates or direct content, accept request data, expose actions, compose other widgets, define named slots, integrate with HTMX, and support lazy loading, refreshing, permissions, and caching.

## Features

* Class-based and function-based widgets
* Automatic widget registration
* Template-based or direct HTML content
* Request-aware widgets
* Query parameters and request data
* Widget composition
* Child widgets
* Named slots
* Widget actions
* Permission-aware rendering
* Lazy loading
* HTMX integration
* Automatic refresh
* Widget endpoints
* Model and queryset support
* Object and multiple-object selection
* Optional widget caching

## Requirements

* Python 3.12+
* Django 5.0+

## Installation

```bash
pip install djangospice-widget
```

Add the package to `INSTALLED_APPS`:

```python
INSTALLED_APPS = [
    # ...
    "djangospice_widget",
]
```

## Defining Widgets

### Class-Based Widgets

A widget is a reusable UI unit.

```python
from djangospice_widget import Widget


class StudentStatisticsWidget(Widget):
    name = "student_statistics"
    title = "Student Statistics"
    template_name = "students/widgets/statistics.html"

    def get_context(self):
        context = super().get_context()
        context["students"] = self.get_queryset()
        return context
```

Widgets have a stable key based on their application and name:

```text
students.student_statistics
```

### Function-Based Widgets

For simple widgets, a function can be used instead of defining a class.

```python
from djangospice_widget import widget


@widget(
    name="welcome",
    title="Welcome",
    template="dashboard/widgets/welcome.html",
)
def welcome_widget(widget):
    return {
        "message": "Welcome to ScholarMIS",
    }
```

Function-based widgets are useful when a dedicated widget class is unnecessary.

## Widget Configuration

Widgets can define metadata and behavior through class attributes.

```python
class StudentStatisticsWidget(Widget):
    name = "student_statistics"
    title = "Student Statistics"
    description = "Summary of current student records."
    group = "students"

    template_name = "students/widgets/statistics.html"

    permission = "students.view_student"

    enabled = True
    priority = 100
```

Common configuration options include:

| Option             | Purpose                        |
| ------------------ | ------------------------------ |
| `name`             | Widget name                    |
| `title`            | Human-readable title           |
| `description`      | Widget description             |
| `group`            | Logical grouping               |
| `template_name`    | Widget template                |
| `permission`       | Required Django permission     |
| `enabled`          | Enables or disables the widget |
| `priority`         | Ordering priority              |
| `lazy`             | Enables lazy loading           |
| `refreshable`      | Enables automatic refresh      |
| `refresh_interval` | Refresh interval               |
| `cache_timeout`    | Enables widget caching         |
| `model`            | Associated Django model        |

## Widget Identity

Every widget has a stable widget key:

For example:

```text
students.student_statistics
```

Widget keys provide a consistent way to reference registered widgets.

## Rendering Widgets

Load the widget template tags:

```django
{% load djangospice_widget %}
```

A registered widget can be rendered by its key:

```django
{% render_widget "students.student_statistics" %}
```

Parameters can be passed to the widget:

```django
{% render_widget "students.student_statistics" campus=campus %}
```

The current Django request is automatically available to the widget.

### Rendering from Python

Widgets can also be rendered directly from Python:

```python
from djangospice_widget import WidgetRenderer

widget = StudentStatisticsWidget(request=request)

html = WidgetRenderer(widget).render()
```

## Widget Content and Templates

Widgets can provide direct content:

```python
class MessageWidget(Widget):

    def get_content(self):
        return "<strong>Hello</strong>"
```

Or render a template using context:

```python
class MessageWidget(Widget):
    template_name = "messages/message.html"

    def get_context(self):
        context = super().get_context()
        context["message"] = "Hello"
        return context
```

Templates are recommended for reusable UI.

## Widget Composition

Widgets can contain other widgets.

For example:

```text
Dashboard
├── Student Statistics
├── Attendance Summary
└── Recent Registrations
```

A parent widget can define its children:

```python
class DashboardWidget(Widget):
    template_name = "dashboard/dashboard.html"

    def configure(self):
        self.add_children(
            StudentStatisticsWidget(request=self.request),
            AttendanceSummaryWidget(request=self.request),
            RecentRegistrationsWidget(request=self.request),
        )
```

The children form part of the parent's widget composition.

### Rendering Children

A widget's children can be rendered from its template:

```django
{% render_children widget %}
```

For example:

```django
<div class="dashboard">
    {% render_children widget %}
</div>
```

`render_children` operates on the current widget instance.

## Named Slots

Widgets can provide named areas for extending their content.

For example, a dashboard can provide a toolbar:

```python
class DashboardWidget(Widget):

    def configure(self):
        self.add_to_slot(
            "toolbar",
            RefreshButtonWidget(request=self.request),
        )

        self.add_children(
            StudentStatisticsWidget(request=self.request),
            AttendanceSummaryWidget(request=self.request),
        )
```

The template can render the slot:

```django
<div class="dashboard">

    <div class="dashboard-toolbar">
        {% render_slot widget "toolbar" %}
    </div>

    <div class="dashboard-content">
        {% render_children widget %}
    </div>

</div>
```

Slots are useful for creating reusable container widgets with extension points.

### Children and Slots

Children and slots serve different purposes.

**Children** represent the normal contents of a widget:

```django
{% render_children widget %}
```

**Slots** provide named extension points:

```django
{% render_slot widget "toolbar" %}
```

A widget can therefore define a reusable structure while allowing other widgets to populate specific areas.

## Template Tags

The package provides three primary rendering tags.

### `render_widget`

Renders a registered widget using its widget key:

```django
{% render_widget "students.statistics" %}
```

### `render_children`

Renders the children of an existing widget:

```django
{% render_children widget %}
```

### `render_slot`

Renders widgets assigned to a named slot:

```django
{% render_slot widget "toolbar" %}
```

The inputs are intentionally different:

| Tag               | Input                  | Purpose                        |
| ----------------- | ---------------------- | ------------------------------ |
| `render_widget`   | Widget key             | Render a registered widget     |
| `render_children` | Widget instance        | Render the widget's children   |
| `render_slot`     | Widget instance + slot | Render widgets in a named slot |

Widget keys are used to reference registered widgets, while widget instances are used to compose existing widget trees.

## Request Awareness

Widgets receive the current Django request.

```python
class CurrentUserWidget(Widget):

    def get_context(self):
        context = super().get_context()
        context["user"] = self.user
        return context
```

Widgets can access request-related information through:

```python
widget.request
widget.user
widget.request_data
```

GET requests expose query parameters, while modifying requests expose submitted request data.

## Query State and URLs

Widgets can work with the current query state:

```python
widget.query_state
```

Widget URLs can preserve or modify query parameters:

```python
widget.url(page=2)
```

This is useful for:

* filtering;
* pagination;
* sorting;
* tabs;
* search;
* other stateful interfaces.

## Widget Endpoints

Registered widgets have a canonical endpoint:

```python
widget.endpoint
```

Widget endpoints can be used for HTMX requests and other widget interactions.

## HTMX

Widgets can progressively enhance server-rendered interfaces with HTMX.

### Lazy Loading

Enable lazy loading with:

```python
class StatisticsWidget(Widget):
    lazy = True
```

The widget can initially display a placeholder and load its content from its endpoint.

### Automatic Refresh

Widgets can periodically refresh their content:

```python
class StatisticsWidget(Widget):
    refreshable = True
    refresh_interval = 30
```

This is useful for dashboards, counters, status information, and other dynamic UI.

## Permissions and Visibility

Widgets can declare a Django permission:

```python
class StudentStatisticsWidget(Widget):
    permission = "students.view_student"
```

Widgets can also implement application-specific visibility rules:

```python
class StudentStatisticsWidget(Widget):

    def is_visible(self):
        return self.user.is_staff
```

This allows widgets to follow both Django permissions and application-specific rules.

## Widget Actions

Widgets can expose reusable actions:

```python
class ViewStudent(Action):
    ...


class EditStudent(Action):
    ...


class DeleteStudent(Action):
    ...
```

Actions can be declared together:

```python
class StudentTableWidget(Widget):

    row_actions = Actions(
        ViewStudent,
        EditStudent,
        DeleteStudent,
    )
```

Multiple action collections can be declared and composed, including nested collections.

Actions can be invoked through the widget's interaction endpoint.

## HTTP Methods

Widgets can respond to HTTP methods:

```python
class StudentWidget(Widget):

    def get(self):
        ...

    def post(self):
        ...

    def delete(self):
        ...
```

GET is the default rendering operation.

Other methods can be implemented for interactive widgets and operations.

## Models and Querysets

Widgets can optionally be associated with a Django model:

```python
class StudentListWidget(Widget):
    model = Student
```

The widget can access its queryset through:

```python
widget.get_queryset()
```

The queryset can be customized:

```python
class StudentListWidget(Widget):
    model = Student

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .filter(active=True)
        )
```

Widgets can also resolve selected objects:

```python
widget.get_object()
widget.get_objects()
```

The default selection parameters are:

```text
selected_id
selected_ids
```

## Caching

Widgets can optionally cache rendered output:

```python
class StatisticsWidget(Widget):
    cache_timeout = 300
```

Caching can be useful for widgets that perform expensive operations, such as:

* dashboards;
* statistics;
* reports;
* summaries;
* expensive database queries.

## Complete Example

### Widget

```python
from djangospice_widget import Widget


class DashboardWidget(Widget):
    name = "dashboard"
    title = "Dashboard"
    template_name = "dashboard/dashboard.html"

    def configure(self):
        self.add_children(
            StudentStatisticsWidget(
                request=self.request,
            ),
            AttendanceSummaryWidget(
                request=self.request,
            ),
        )

        self.add_to_slot(
            "toolbar",
            RefreshButtonWidget(
                request=self.request,
            ),
        )
```

### Template

```django
{% load djangospice_widget %}

<div class="dashboard">

    <header class="dashboard-header">
        <h1>{{ widget.title }}</h1>

        <div class="dashboard-toolbar">
            {% render_slot widget "toolbar" %}
        </div>
    </header>

    <main class="dashboard-content">
        {% render_children widget %}
    </main>

</div>
```

### Usage

```django
{% render_widget "dashboard.dashboard" %}
```

## License

This package is licensed under the **MIT License**.

See [LICENSE](LICENSE) for the full license text.
