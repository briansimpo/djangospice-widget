# djangospice-widget

Reusable, composable, request-aware UI widgets for Django.

`djangospice-widget` provides a class-based widget system for building server-rendered Django interfaces from small, reusable UI units.

Widgets can render templates or direct HTML content, access request data, expose actions, compose other widgets, define named slots, integrate with HTMX, support permissions, and work with Django models and querysets.

## Features

- Class-based widgets
- Automatic widget registration
- Template-based rendering
- Direct HTML content rendering
- Request-aware widgets
- Request data and query parameters
- Widget composition
- Child widgets
- Named slots
- Widget actions
- Permission-aware visibility
- Custom visibility rules
- Lazy loading
- HTMX integration
- Automatic refresh
- Widget endpoints
- Stateful widget URLs
- Model and queryset support
- Object and multiple-object selection
- Optional widget caching
- HTTP method handling

## Requirements

- Python 3.12+
- Django 5.0+

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

---

## Defining Widgets

A widget is a reusable, class-based UI component.

```python
from djangospice_widget import Widget


class StudentStatisticsWidget(Widget):
    template_name = "students/widgets/statistics.html"

    def get_context(self):
        context = super().get_context()
        context["students"] = self.get_queryset()
        context["total"] = self.get_queryset().count()
        return context
```

Instantiate a widget with the current request:

```python
widget = StudentStatisticsWidget(request=request)
```

---

## Widget Identity

Widgets have a stable identity based on their application and name.

```python
class StudentStatisticsWidget(Widget):
    ...
```

The widget automatically derives a name and title:

```text
name  -> student-statistics
title -> Student Statistics
```

You can explicitly define them:

```python
class StudentStatisticsWidget(Widget):
    name = "student-statistics"
    title = "Student Statistics"
```

The widget key is available through:

```python
widget.widget_key
```

For example:

```text
students.student-statistics
```

Widget keys can be used to reference registered widgets.

---

## Widget Configuration

Widgets can define metadata and behavior through class attributes.

```python
class StudentStatisticsWidget(Widget):
    name = "student-statistics"
    title = "Student Statistics"
    description = "Summary of current student records."

    template_name = "students/widgets/statistics.html"

    permission = "students.view_student"

    enabled = True
    priority = 100
```

Common configuration options include:

| Option | Purpose |
| --- | --- |
| `name` | Widget name |
| `title` | Human-readable title |
| `app_label` | Django application label |
| `description` | Widget description |
| `template_name` | Widget template |
| `permission` | Required Django permission |
| `enabled` | Enables or disables the widget |
| `priority` | Ordering priority |
| `lazy` | Enables lazy loading |
| `refreshable` | Enables automatic refresh |
| `refresh_interval` | Refresh interval in seconds |
| `cache_timeout` | Enables widget caching |
| `model` | Associated Django model |

---

## Rendering Widgets

Load the widget template tags:

```django
{% load djangospice_widget %}
```

A registered widget can be rendered using its widget key:

```django
{% render_widget "students.student-statistics" %}
```

Parameters can be passed to the widget:

```django
{% render_widget "students.student-statistics" campus=campus %}
```

The current Django request is automatically available to the widget.

### Rendering from Python

Widgets can also be rendered directly:

```python
widget = StudentStatisticsWidget(
    request=request,
)

html = widget.render()
```

For an HTTP response:

```python
response = widget.response()
```

For example:

```python
def student_dashboard(request):
    widget = StudentStatisticsWidget(
        request=request,
    )

    return widget.response()
```

---

## Widget Content and Templates

Widgets can provide direct HTML content:

```python
from django.utils.html import format_html


class MessageWidget(Widget):

    def get_content(self):
        return format_html(
            "<strong>Hello</strong>"
        )
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

Template-based widgets can use the standard Django template system.

---

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
            StudentStatisticsWidget(
                request=self.request,
            ),
            AttendanceSummaryWidget(
                request=self.request,
            ),
            RecentRegistrationsWidget(
                request=self.request,
            ),
        )
```

Children can be rendered from the template:

```django
{% render_children widget %}
```

For example:

```django
<div class="dashboard">
    {% render_children widget %}
</div>
```

---

## Named Slots

Widgets can provide named areas for extending their content.

For example, a dashboard can provide a toolbar:

```python
class DashboardWidget(Widget):

    def configure(self):
        self.add_to_slot(
            "toolbar",
            RefreshButtonWidget(
                request=self.request,
            ),
        )

        self.add_children(
            StudentStatisticsWidget(
                request=self.request,
            ),
            AttendanceSummaryWidget(
                request=self.request,
            ),
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

Slots are useful for reusable container widgets with named extension areas.

### Children and Slots

**Children** represent the normal contents of a widget:

```django
{% render_children widget %}
```

**Slots** provide named extension points:

```django
{% render_slot widget "toolbar" %}
```

---

## Template Tags

The package provides three primary rendering tags.

### `render_widget`

Renders a registered widget using its widget key:

```django
{% render_widget "students.student-statistics" %}
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

| Tag | Input | Purpose |
| --- | --- | --- |
| `render_widget` | Widget key | Render a registered widget |
| `render_children` | Widget instance | Render widget children |
| `render_slot` | Widget instance + slot | Render widgets in a named slot |

---

## Request Awareness

Widgets receive the current Django request.

```python
class CurrentUserWidget(Widget):

    def get_context(self):
        context = super().get_context()
        context["user"] = self.user
        return context
```

Widgets can access:

```python
widget.request
widget.user
widget.request_data
```

GET requests expose query parameters, while modifying requests expose submitted request data.

Individual values can be accessed with:

```python
widget.request_value("status")
```

Multiple values can be accessed with:

```python
widget.request_values("selected_ids")
```

---

## Query State and URLs

Widgets can access the current query state:

```python
widget.query_state
```

Widget URLs can preserve or modify query parameters:

```python
widget.url(page=2)
```

Multiple parameters can be supplied:

```python
widget.url(
    page=2,
    status="active",
)
```

This is useful for:

- filtering
- pagination
- sorting
- tabs
- searching
- stateful interfaces

---

## Widget Endpoints

Registered widgets have a canonical endpoint:

```python
widget.endpoint
```

Widget endpoints can be used for:

- HTMX requests
- lazy loading
- automatic refresh
- widget interactions

---

## HTMX

Widgets can progressively enhance server-rendered interfaces with HTMX.

### Lazy Loading

Enable lazy loading with:

```python
class StatisticsWidget(Widget):
    lazy = True
```

Lazy widgets can load their content from their widget endpoint.

### Automatic Refresh

Widgets can periodically refresh their content:

```python
class StatisticsWidget(Widget):
    refreshable = True
    refresh_interval = 30
```

This is useful for:

- dashboards
- counters
- status information
- dynamic statistics

### HTMX Interactions

Widgets can create interactions:

```python
interaction = widget.interaction(
    "/students/",
    method="GET",
    target="#student-list",
)
```

Options include:

- HTTP method
- target
- swap strategy
- URL behavior

---

## Permissions and Visibility

Widgets can declare a Django permission:

```python
class StudentStatisticsWidget(Widget):
    permission = "students.view_student"
```

Check whether a widget is visible:

```python
widget.visible()
```

Explicitly enforce visibility:

```python
widget.authorize()
```

Application-specific visibility rules can also be defined:

```python
class StudentStatisticsWidget(Widget):

    def is_visible(self):
        return self.user.is_staff
```

---

## Widget Actions

Widgets can expose reusable actions.

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

Multiple action collections can be declared and composed.

Access the widget's actions with:

```python
widget.get_action_collection()
```

---

## HTTP Methods

Widgets can respond to HTTP methods:

```python
class StudentWidget(Widget):

    def get(self):
        return self.response()

    def post(self):
        ...

    def put(self):
        ...

    def patch(self):
        ...

    def delete(self):
        ...
```

GET is the default rendering operation.

Other methods can be implemented for interactive widgets and server-side operations.

---

## Models and Querysets

Widgets can optionally be associated with a Django model:

```python
class StudentListWidget(Widget):
    model = Student
```

Access the queryset through:

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

---

## Object Selection

Widgets can resolve a selected object:

```python
widget.get_object()
```

Multiple selected objects can be resolved with:

```python
widget.get_objects()
```

The default selection parameters are:

```text
selected_id
selected_ids
```

These can be customized:

```python
class StudentWidget(Widget):
    object_parameter = "student_id"
    objects_parameter = "student_ids"
```

---

## Caching

Widgets can optionally enable caching:

```python
class StatisticsWidget(Widget):
    cache_timeout = 300
```

Caching can be useful for:

- dashboards
- statistics
- reports
- summaries
- expensive database queries

---

# Complete Example

## Widget

```python
from djangospice_widget import Widget


class DashboardWidget(Widget):
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

## Template

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

## Usage in a Template

```django
{% render_widget "dashboard.dashboard" %}
```

## Usage from Python

```python
def dashboard(request):
    widget = DashboardWidget(
        request=request,
    )

    return widget.response()
```

---

## License

This package is licensed under the **MIT License**.

See [LICENSE](LICENSE) for the full license text.