from __future__ import annotations

from abc import abstractmethod
from typing import ClassVar

from django.core.exceptions import PermissionDenied

from djangospice_framework.core.object import Object
from djangospice_framework.html.attributes import HTMXAttributes
from djangospice_framework.response.response import Response

from .context import ActionContext
from .metaclass import ActionMetaclass


class Action(Object, metaclass=ActionMetaclass):
    """Base executable widget action.

    Represents a discrete, repeatable operation that can be triggered from a widget UI,
    typically executed via an HTMX request. Handles visibility, permissions, lifecycle 
    hooks, and dynamic HTMX attribute generation.
    """

    # ------------------------------------------------------------------
    # Identity
    # ------------------------------------------------------------------

    name: ClassVar[str | None] = None
    """Internal programmatic identifier for the action (e.g., 'delete_user')."""

    label: ClassVar[str | None] = None
    """Human-readable display text rendered on the button/link."""

    # ------------------------------------------------------------------
    # Presentation
    # ------------------------------------------------------------------

    icon: ClassVar[str | None] = None
    """Optional icon identifier/class to render alongside the label."""

    description: ClassVar[str | None] = None
    """Optional tooltip or descriptive text explaining the action's purpose."""

    css_class: ClassVar[str | None] = None
    """Custom CSS classes applied to the action's trigger element."""

    order: ClassVar[int] = 100
    """Sorting priority for UI rendering (lower numbers appear first)."""

    # ------------------------------------------------------------------
    # Behaviour
    # ------------------------------------------------------------------

    method: ClassVar[str] = "POST"
    """HTTP method used to dispatch this action via HTMX."""

    permission: ClassVar[str | None] = None
    """Django permission string required to execute this action (e.g., 'app.delete_model')."""

    confirm: ClassVar[str | None] = None
    """Optional confirmation message injected as an `hx-confirm` attribute."""

    # ------------------------------------------------------------------
    # State
    # ------------------------------------------------------------------

    def visible(self, context: ActionContext) -> bool:
        """Determines if the action should be rendered in the UI.

        Args:
            context: The current action execution context.

        Returns:
            True if the action element should be displayed.
        """
        return True

    def enabled(self, context: ActionContext) -> bool:
        """Determines if the action is interactive or disabled/greyed out.

        Args:
            context: The current action execution context.

        Returns:
            True if the action is currently executable.
        """
        return True

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def authorize(self, context: ActionContext) -> None:
        """Validates execution privileges before the action runs.

        Automatically enforces `self.permission` if declared.
        Override to add custom business logic authorization.

        Args:
            context: The current action execution context.

        Raises:
            PermissionDenied: If execution is not allowed for the current user.
        """
        if self.permission and context.request and context.request.user:
            if not context.request.user.has_perm(self.permission):
                raise PermissionDenied(
                    f"User lacks required permission: '{self.permission}'"
                )

    def before_execute(self, context: ActionContext) -> None:
        """Lifecycle hook executed immediately before `execute()`.

        Useful for logging, state preparation, or pre-validation.
        """
        pass

    def after_execute(self, context: ActionContext) -> None:
        """Lifecycle hook executed immediately after `execute()`.

        Useful for cleanup or audit logging.
        """
        pass

    # ------------------------------------------------------------------
    # HTMX
    # ------------------------------------------------------------------

    def htmx(self, context: ActionContext) -> HTMXAttributes:
        """Generates the requisite HTMX attributes for triggering this action.

        Args:
            context: The current action execution context.

        Returns:
            An HTMXAttributes builder pre-configured with URL, method, and parameters.
        """
        attributes = (
            HTMXAttributes()
            .request(
                method=self.method,
                url=context.widget.endpoint,
            )
            .with_vals(
                action=self.name,
            )
        )

        if context.object is not None:
            attributes.with_vals(selected_id=str(context.object.pk))

        # Dynamically append confirmation prompt if defined
        if self.confirm:
            # Assuming HTMXAttributes allows attribute injection. 
            # If your framework uses a specific method like .confirm(), update accordingly.
            attributes.confirm_with(self.confirm)

        return attributes
            
    def dispatch(self, context: ActionContext) -> Response:
        """Coordinates the action lifecycle and handles execution.

        Enforces state checks, authorization, and hooks in the correct sequence.

        Args:
            context: The current action execution context.

        Returns:
            A framework Response object to be parsed by the widget view.
        
        Raises:
            PermissionDenied: If the action is disabled or unauthorized.
        """
        if not self.enabled(context):
            raise PermissionDenied(f"Action '{self.name}' is disabled.")

        self.authorize(context)
        self.before_execute(context)
        
        response = self.execute(context)
        
        self.after_execute(context)

        return response

    # ------------------------------------------------------------------
    # Execute
    # ------------------------------------------------------------------

    @abstractmethod
    def execute(self, context: ActionContext) -> Response:
        """The core business logic of the action.

        Must be implemented by subclasses.

        Args:
            context: Context containing the request, widget state, and target objects.

        Returns:
            A Response instructing the framework how to reply (e.g., HTMX triggers).
        """
        raise NotImplementedError