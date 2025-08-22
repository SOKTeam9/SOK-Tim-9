from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name="index"),
    path("block-visualizer/", views.block_view, name="block_visualizer"),
    path("graph-block-data/", views.graph_block_data, name="graph_block_data"),
]