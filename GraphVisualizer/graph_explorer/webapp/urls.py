from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name="index"),
    path('simpleVisualizer/', views.simple_visualizer, name="simple_visualizer"),
    path('fileInput/', views.load_file, name="load_file"),
    path('search/', views.make_search, name="query"),
    path('resetFilters/', views.reset_graph, name="reset_graph")
]