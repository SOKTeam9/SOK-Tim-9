from django.apps import apps
from django.shortcuts import render, redirect
from plugins.visualizer_simple.simple_visualizer import SimpleVisualizer
from platforms.graph_handler import GraphHandler

def index(request):
    return render(request, 'index.html', {'title': 'Index'})

def simple_visualizer(request):
    handler = GraphHandler("neo4j://127.0.0.1:7687", "neo4j", "djomlaboss")
    simple = SimpleVisualizer()
    simple.render(handler.get_graph())
    handler.close()
    return render(request, 'simple-template.html')