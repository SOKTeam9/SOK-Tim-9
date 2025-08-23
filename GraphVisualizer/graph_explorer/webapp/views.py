from django.apps import apps
from django.shortcuts import render, redirect
from plugins.visualizer_simple.simple_visualizer import SimpleVisualizer
from platforms.graph_handler import GraphHandler
from plugins.data_source_plugin_yaml.yaml_data_source_plugin import YamlFileParser
from neo4j import GraphDatabase
import os
import tempfile

filters = []

def index(request):
    return render(request, 'index.html', {'title': 'Index'})

# def simple_visualizer(request):
#     print("PROBAAA")
#     handler = GraphHandler("neo4j://127.0.0.1:7687", "neo4j", "djomlaboss")
#     simple = SimpleVisualizer()
#     simple.render(handler.get_graph())
#     handler.close()
#     return render(request, 'simple-template.html')

def simple_visualizer(request):
    handler = GraphHandler("neo4j://127.0.0.1:7687", "neo4j", "djomlaboss")
    graph_data = handler.get_graph()
    visualizer = SimpleVisualizer()
    context = visualizer.get_context(graph_data)
    return render(request, "simple_template.html", context)

def load_file(request):
     if request.method == "POST":
        uploaded_file = request.FILES.get("load_file")
        if uploaded_file:
            uri = "neo4j://127.0.0.1:7687"
            username = "neo4j"
            password = "djomlaboss"

            # Kreiranje drajvera
            driver = GraphDatabase.driver(uri, auth=(username, password))

            file_type = uploaded_file.name.split(".")[1]
            # Napravi privremeni fajl sa suffix .yaml
            with tempfile.NamedTemporaryFile(delete=False, suffix=file_type) as tmp:
                for chunk in uploaded_file.chunks():
                    tmp.write(chunk)
                tmp_path = tmp.name  # privremena putanja fajla

            parser = YamlFileParser(tmp_path, driver)
            parser.load()
            # Zatvaranje drajvera
            driver.close()

            # Možeš odmah obrisati privremeni fajl
            os.remove(tmp_path)
            return simple_visualizer(request)

def make_search(request):
    if request.method == "POST":
        search_query = request.POST.get("search", "").strip()
        if search_query != "":
            attribute = search_query.split("-")[0]
            operator = search_query.split("-")[1]
            value = search_query.split("-")[2]
            try:
                actual_value = float(value)
            except:
                actual_value = value
            filters.append((attribute, operator, actual_value))
            handler = GraphHandler("neo4j://127.0.0.1:7687", "neo4j", "djomlaboss")
            graph_data = handler.get_subgraph(filters)
            visualizer = SimpleVisualizer()
            context = visualizer.get_context(graph_data)
            return render(request, "simple_template.html", context)


