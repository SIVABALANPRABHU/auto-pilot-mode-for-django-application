from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path("create-app/", views.create_app, name="create_app"),
]
