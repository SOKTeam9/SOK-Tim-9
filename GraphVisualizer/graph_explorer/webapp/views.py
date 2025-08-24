from django.apps import apps
from django.shortcuts import render, redirect
from django.http import JsonResponse
from platforms.graph_handler import GraphHandler
from neo4j.time import Date, DateTime
from plugins.visualizer_block.block_visualizer import BlockVisualizer
import json
import datetime

# URI obavezno promeni u "bolt://..." umesto neo4j://, jer ti je single instance
handler = GraphHandler("neo4j://127.0.0.1:7687", "neo4j", "djomlaboss")

from plugins.visualizer_simple.simple_visualizer import SimpleVisualizer
from platforms.graph_handler import GraphHandler

def index(request):
    return render(request, 'index.html', {'title': 'Index'})

class Neo4jJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        # Neo4j datumi
        if isinstance(obj, (Date, DateTime)):
            return str(obj)  # '2025-08-20' ili '2025-08-20 14:55:00'

        # Python datumi
        if isinstance(obj, (datetime.date, datetime.datetime)):
            return obj.isoformat()  # '2025-08-20T14:55:00'

        return super().default(obj)


def graph_block_data(request):
    handler = GraphHandler("neo4j://127.0.0.1:7687", "neo4j", "djomlaboss")
    return JsonResponse(
    handler.get_graph(),
    safe=False,
    encoder=Neo4jJSONEncoder)

def block_view(request):
    handler = GraphHandler("neo4j://127.0.0.1:7687", "neo4j", "djomlaboss")
    graph_data = handler.get_graph()  # vraća nodes + links

    visualizer = BlockVisualizer(graph_data)
    html = visualizer.render()

    return render(request, "block-template.html", {"graph_json": graph_data})

def simple_visualizer(request):
    handler = GraphHandler("neo4j://127.0.0.1:7687", "neo4j", "djomlaboss")
    graph_data = handler.get_graph()
    visualizer = SimpleVisualizer()
    context = visualizer.get_context(graph_data)
    return render(request, "simple_template.html", context)

def load_file(request):
    pass
