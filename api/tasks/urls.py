from django.urls import path
from .views import TaskViewSet
import os

app_name = os.getcwd().split(os.sep)[-1]

urlpatterns = [
    path("", TaskViewSet.as_view({"post": "create", "get": "list"}), name="tasks"),
]
