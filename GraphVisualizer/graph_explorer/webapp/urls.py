from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name="index"),
    path('simpleVisualizer/', views.simple_visualizer, name="simple_visualizer"),
    path('fileInput/', views.load_file, name="load_file"),
    path('search/', views.make_search, name="query_search"),
    path('resetFilters/', views.reset_graph, name="reset_graph"),
    path('filters/', views.apply_filter, name="query_filter"),
    path("block-visualizer/", views.block_view, name="block_visualizer"),
    path("graph-block-data/", views.graph_block_data, name="graph_block_data"),
    path('create_node/', views.create_node, name='create_node'),
]