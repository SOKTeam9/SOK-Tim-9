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
    path('edit_node/', views.edit_node, name='edit_node'),
    path('delete_node/', views.delete_node, name='delete_node'),
    path('create_edge/', views.create_edge, name='create_edge'),
    path('edit_edge/', views.edit_edge, name='edit_edge'),
]