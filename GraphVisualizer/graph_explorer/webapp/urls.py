from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name="index"),
    path('simpleVisualizer/ws=<int:ws_id>/', views.simple_visualizer, name="simple_visualizer"),
    path('fileInput/ws=<int:ws_id>/', views.load_file, name="load_file"),
    path('search/ws=<int:ws_id>/', views.make_search, name="query_search"),
    path('resetFilters/ws=<int:ws_id>/', views.reset_graph, name="reset_graph"),
    path('filters/ws=<int:ws_id>/', views.apply_filter, name="query_filter"),
    path("block-visualizer/ws=<int:ws_id>/", views.block_view, name="block_visualizer"),
    path("graph-block-data/ws=<int:ws_id>/", views.graph_block_data, name="graph_block_data"),
    path("filter-remove/ws=<int:ws_id>/", views.filter_remove, name="filter_remove"),
    path("workspace_switch/ws=<int:ws_id>/", views.workspace_switch, name="workspace_switch")
]