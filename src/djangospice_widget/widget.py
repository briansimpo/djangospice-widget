from __future__ import annotations

from copy import deepcopy
from typing import Any, ClassVar
from urllib.parse import urlencode

from django.apps import apps
from django.contrib.auth.models import AbstractBaseUser, AnonymousUser
from django.core.exceptions import AppRegistryNotReady
from django.db.models import Model, QuerySet
from django.http import HttpRequest
from django.urls import reverse

from djangospice_framework.core.payload import Payload
from djangospice_framework.html.component import HTMLComponent
from djangospice_framework.response.response import Response

from .utils import slugify
from .actions import Action, Actions, ActionContext, BoundAction
from .exceptions import WidgetNotVisible
from .identifier import WidgetIdentifier
from .interaction import Interaction
from .navigation import Navigation
from .querystate import QueryState
from .conf import APP_NAME_KEY, MODEL_NAME_KEY


# ==============================================================================
# 1. Identity Component
# ==============================================================================

class IdentityMixin:
    """Handles widget metadata, app label resolution, and keys."""

    name: ClassVar[str | None] = None
    title: ClassVar[str | None] = None
    app_label: ClassVar[str | None] = None
    description: ClassVar[str] = ""

    @classmethod
    def _configure_identity(cls) -> None:
        if cls.name is None:
            cls.name = slugify(cls.__name__)

        if cls.title is None:
            cls.title = cls.name.replace("_", " ").title()

        if cls.app_label is None:
            cls.app_label = cls._resolve_app_label(cls.__module__)

    @classmethod
    def _resolve_app_label(cls, module_path: str) -> str:
        try:
            for app_config in apps.get_app_configs():
                if module_path.startswith(app_config.name):
                    return app_config.label
        except AppRegistryNotReady:
            pass

        parts = module_path.split(".")
        return parts[0] if parts else ""

    @property
    def widget_key(self) -> str:
        return str(WidgetIdentifier(self.app_label, self.name))


# ==============================================================================
# 2. Actions Component
# ==============================================================================

class ActionsMixin:
    """Manages action group declaration, normalization, and execution collections."""

    actions: ClassVar[Actions] = Actions()
    _actions: ClassVar[Actions] = Actions()

    @classmethod
    def _declared_action_groups(cls) -> dict[str, Actions]:
        groups: dict[str, Actions] = {}
        for base in reversed(cls.__mro__):
            for name, value in base.__dict__.items():
                if isinstance(value, Actions):
                    groups[name] = value
        return groups

    @classmethod
    def _normalize_actions(cls) -> None:
        groups = cls._declared_action_groups()
        normalized: dict[str, Actions] = {}

        for name, actions in groups.items():
            if name in cls.__dict__ and isinstance(cls.__dict__[name], Actions):
                collection = Actions(*deepcopy(actions))
                setattr(cls, name, collection)
                normalized[name] = collection
            else:
                normalized[name] = actions

        cls._actions = cls.merge_actions(*normalized.values())

    @classmethod
    def merge_actions(cls, *collections: Actions) -> Actions:
        actions: dict[str, Any] = {}
        for collection in collections:
            for action in collection:
                actions[action.name] = deepcopy(action)
        return Actions(*actions.values())

    def get_action_collection(self) -> Actions:
        return self._actions

    def bind_action(self, action: Action, context: ActionContext) -> BoundAction:
        return BoundAction(
            action=action,
            context=context,
        )


# ==============================================================================
# 3. Composition Component
# ==============================================================================

class CompositionMixin:
    """Manages parent-child hierarchies and named composition slots."""

    parent: Widget | None
    children: list[Widget]
    slots: dict[str, list[Widget]]

    def _init_composition(self, parent: Widget | None = None) -> None:
        self.parent = parent
        self.children = []
        self.slots = {}

    def add_child(self: Widget, widget: Widget) -> Widget:
        self._attach(widget)
        self.children.append(widget)
        return widget

    def add_children(self: Widget, *widgets: Widget) -> tuple[Widget, ...]:
        for widget in widgets:
            self.add_child(widget)
        return widgets

    def remove_child(self: Widget, widget: Widget) -> None:
        if widget not in self.children:
            return
        self.children.remove(widget)
        if widget.parent is self:
            widget.parent = None

    def clear_children(self: Widget) -> None:
        for widget in self.children:
            if widget.parent is self:
                widget.parent = None
        self.children.clear()

    def get_children(self) -> tuple[Widget, ...]:
        return tuple(self.children)

    def set_slot(self: Widget, name: str, *widgets: Widget) -> None:
        self.clear_slot(name)
        for widget in widgets:
            self.add_to_slot(name, widget)

    def add_to_slot(self: Widget, name: str, widget: Widget) -> Widget:
        self._attach(widget)
        self.slots.setdefault(name, []).append(widget)
        return widget

    def add_to_slots(self: Widget, **slots: Widget | list[Widget] | tuple[Widget, ...]) -> None:
        for name, value in slots.items():
            if isinstance(value, Widget):
                self.add_to_slot(name, value)
                continue
            for widget in value:
                self.add_to_slot(name, widget)

    def get_slot(self, name) -> tuple[Widget, ...]:
        return tuple(self.slots.get(name, ()))

    def has_slot(self, name: str) -> bool:
        return bool(self.slots.get(name))

    def remove_from_slot(self: Widget, name: str, widget: Widget) -> None:
        widgets = self.slots.get(name)
        if not widgets or widget not in widgets:
            return
        widgets.remove(widget)
        if widget.parent is self:
            widget.parent = None

    def clear_slot(self: Widget, name: str) -> None:
        for widget in self.slots.get(name, ()):
            if widget.parent is self:
                widget.parent = None
        self.slots.pop(name, None)

    def clear_slots(self: Widget) -> None:
        for name in tuple(self.slots):
            self.clear_slot(name)

    def _attach(self: Widget, widget: Widget) -> None:
        if widget is self:
            raise ValueError("A widget cannot contain itself.")
        widget.parent = self
        if widget.request is None:
            widget.request = getattr(self, "request", None)


# ==============================================================================
# 4. Request & Visibility Component
# ==============================================================================

class RequestVisibilityMixin:
    """Handles request data parsing, authorization, and visibility logic."""

    enabled: ClassVar[bool] = True
    permission: ClassVar[str | None] = None
    priority: ClassVar[int] = 100

    request: HttpRequest | None

    @property
    def user(self) -> AbstractBaseUser | AnonymousUser | None:
        return getattr(self.request, "user", None)

    @property
    def request_data(self) -> Any:
        if self.request is None:
            return None
        if self.request.method in {"POST", "PUT", "PATCH"}:
            return self.request.POST
        return self.request.GET

    def request_value(self, name: str) -> Any:
        data = self.request_data
        return data.get(name) if data is not None else None

    def request_values(self, name: str) -> list[Any]:
        data = self.request_data
        return data.getlist(name) if data is not None else []

    def authorize(self) -> None:
        if not self.visible():
            raise WidgetNotVisible

    def visible(self) -> bool:
        if not self.enabled:
            return False
        if self.permission and not self._has_permission():
            return False
        return self.is_visible()

    def _has_permission(self) -> bool:
        user = self.user
        return bool(user and user.is_authenticated and user.has_perm(self.permission))

    def is_visible(self) -> bool:
        return True


# ==============================================================================
# 5. Data Resolver Component
# ==============================================================================

class DataMixin:
    """Handles ORM model resolution, QuerySets, and Payload building."""

    model: ClassVar[type[Model] | None] = None
    object_parameter: ClassVar[str] = "selected_id"
    objects_parameter: ClassVar[str] = "selected_ids"

    def get_queryset(self) -> QuerySet[Model]:
        if self.model is None:
            raise NotImplementedError(
                f"{self.__class__.__name__} must define 'model' or override 'get_queryset()'."
            )
        return self.model._default_manager.all()

    def get_object(self: Widget) -> Model | None:
        pk = self.request_value(self.object_parameter)
        if not pk:
            return None
        return self.get_queryset().filter(pk=pk).first()

    def get_objects(self: Widget) -> tuple[Model, ...]:
        ids = self.request_values(self.objects_parameter)
        if not ids:
            obj = self.get_object()
            return (obj,) if obj else ()
        return tuple(self.get_queryset().filter(pk__in=ids))

    def get_data(self: Widget) -> Payload:
        data = self.request_data
        if data is None:
            return Payload()
        return Payload.from_dict(data.dict())


# ==============================================================================
# 6. Navigation & HTMX Component
# ==============================================================================

class NavigationMixin:
    """Handles endpoints, URL building, HTMX interactions, and lazy fetching."""

    namespace: ClassVar[str] = "djangospice_widget"
    lazy: ClassVar[bool] = False
    refreshable: ClassVar[bool] = False
    refresh_interval: ClassVar[int | None] = None

    @property
    def navigation(self: Widget) -> Navigation:
        from .navigation import Navigation
        return Navigation(self)

    @property
    def query_state(self: Widget) -> QueryState:
        from .querystate import QueryState
        if self.request is None:
            return QueryState()
        return QueryState.from_querydict(self.request.GET)

    @property
    def base_url(self: Widget) -> str:
        return self.endpoint.split("?", 1)[0]

    @property
    def endpoint(self: Widget) -> str:
        url = reverse(
            self.namespace,
            kwargs={
                APP_NAME_KEY: self.app_label,
                MODEL_NAME_KEY: self.name,
            },
        )
        params = {k: v for k, v in self.kwargs.items() if k != "id"}
        return f"{url}?{urlencode(params)}" if params else url

    @property
    def is_lazy_fetch(self: Widget) -> bool:
        request = self.request
        if request is None or request.headers.get("HX-Request") != "true":
            return False

        match = request.resolver_match
        return bool(
            match
            and match.view_name == self.namespace
            and match.kwargs.get(APP_NAME_KEY) == self.app_label
            and match.kwargs.get(MODEL_NAME_KEY) == self.name
        )

    def url(self: Widget, *, state: QueryState | None = None, **params: Any) -> str:
        state = state or self.query_state
        for name, value in params.items():
            state = state.set(name, value)
        query = state.encode()
        return f"{self.base_url}?{query}" if query else self.base_url
    
    def configure_htmx(self: Widget) -> None:
        if self.lazy:
            (
                self.htmx
                .get(self.endpoint)
                .trigger_on("load")
                .target_to("this")
                .swap_to("outerHTML")
            )

        if self.refreshable and self.refresh_interval:
            trigger = getattr(self.htmx, "trigger", None) or "load"
            (
                self.htmx
                .trigger_on(f"{trigger}, every {self.refresh_interval}s")
                .target_to("this")
            )

    def interaction(
        self: Widget,
        url: str,
        *,
        method: str = "GET",
        target: str | None = None,
        swap: str = "outerHTML",
        push_url: bool = True,
    ) -> Interaction:
        from .interaction import Interaction
        htmx = (
            self.htmx
            .request(method=method, url=url)
            .target_to(target or "this")
            .swap_to(swap)
        )
        if push_url:
            htmx = htmx.push_url(url)
        return Interaction(url=url, htmx=htmx)


# ==============================================================================
# 7. Caching Component
# ==============================================================================

class CacheMixin:
    """Handles widget cache keys, state hashes, and evaluation timeouts."""

    cache_timeout: ClassVar[int | None] = None

    def should_cache(self) -> bool:
        return self.cache_timeout is not None

    def cache_key(self: CacheMixin | IdentityMixin | RequestVisibilityMixin | Widget) -> str:
        return ":".join(
            (
                self.namespace,
                self.widget_key,
                self.cache_identifier(),
                self.generate_state_hash(),
            )
        )

    def cache_identifier(self: RequestVisibilityMixin) -> str:
        user = self.user
        return str(user.pk) if user and user.is_authenticated else "anonymous"

    def generate_state_hash(self) -> str:
        return "default"


# ==============================================================================
# 8. HTTP Component
# ==============================================================================

class HttpMixin:
    """Handles HTTP response dispatch and template context rendering."""

    template_name: ClassVar[str] = ""

    def get_context(self: Widget) -> dict[str, Any]:
        context = super().get_context()
        context.update(
            widget=self,
            request=self.request,
            children=self.get_children(),
            slots=self.slots,
        )
        return context

    def response(self: Widget) -> Response:
        return Response.make(self.template_name, **self.get_context())

    def get(self: Widget) -> Response:
        return self.response()

    def post(self) -> Response:
        return self.method_not_allowed()

    def put(self) -> Response:
        return self.method_not_allowed()

    def patch(self) -> Response:
        return self.method_not_allowed()

    def delete(self) -> Response:
        return self.method_not_allowed()

    def method_not_allowed(self) -> Response:
        return Response.empty(status=405)


# ==============================================================================
# 9. Widget Orchestrator
# ==============================================================================

class Widget(
    IdentityMixin,
    ActionsMixin,
    CompositionMixin,
    RequestVisibilityMixin,
    DataMixin,
    NavigationMixin,
    CacheMixin,
    HttpMixin,
    HTMLComponent,
):
    """
    Base class for Djangospice UI widgets.

    Coordinates presentation, state, composition, security, and execution 
    across component mixins.
    """

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        cls._configure_identity()
        cls._normalize_actions()

    def __init__(
        self,
        request: HttpRequest | None = None,
        *,
        parent: Widget | None = None,
        children: list[Widget] | None = None,
        slots: dict[str, list[Widget]] | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(kwargs=kwargs)

        self.request = request
        self._init_composition(parent=parent)

        self.initialize()
        self.configure()

        if children:
            self.add_children(*children)

        if slots:
            for name, widgets in slots.items():
                self.set_slot(name, *widgets)

    def initialize(self) -> None:
        """Post-construction initialization hook."""
        pass

    def configure(self) -> None:
        """Instance-level composition and slot population hook."""
        pass


