from django.urls import path

from .apps import namespace
from .views import WidgetView
from .conf import APP_NAME_URL_KEY, MODEL_NAME_URL_KEY

urlpatterns = [
    path(
        f"widgets/{APP_NAME_URL_KEY}>/{MODEL_NAME_URL_KEY}/", 
        WidgetView.as_view(),
        name=namespace,
    ),

]