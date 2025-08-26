from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name="index"),
    path('create_node/', views.create_node, name='create_node'),
    path('edit_node/', views.edit_node, name='edit_node'),
    path('delete_node/', views.delete_node, name='delete_node'),
    path('create_edge/', views.create_edge, name='create_edge'),
    path('edit_edge/', views.edit_edge, name='edit_edge'),
    path('delete_edge/', views.delete_edge, name='delete_edge'),
    path('cli_search/ws=<int:ws_id>/', views.cli_search, name='cli_search'),
    path('clear_database/ws=<int:ws_id>/', views.clear_database, name='clear_database'),
    path('simpleVisualizer/ws=<int:ws_id>/', views.simple_visualizer, name="simple_visualizer"),
    path('fileInput/ws=<int:ws_id>/', views.load_file, name="load_file"),
    path('search/ws=<int:ws_id>/', views.make_search, name="query_search"),
    path('resetFilters/ws=<int:ws_id>/', views.reset_graph, name="reset_graph"),
    path('filters/ws=<int:ws_id>/', views.apply_filter, name="query_filter"),
    path("block-visualizer/ws=<int:ws_id>/", views.block_view, name="block_visualizer"),
    path("graph-block-data/ws=<int:ws_id>/", views.graph_block_data, name="graph_block_data"),
    path("filter-remove/ws=<int:ws_id>/", views.filter_remove, name="filter_remove"),
    path("workspace_switch/ws=<int:ws_id>/", views.workspace_switch, name="workspace_switch"),
    path("redirect/", views.redirect, name="redirect"),
]