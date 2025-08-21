from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name="index"),
    path('simpleVisualizer/', views.simple_visualizer, name="simple_visualizer")
]