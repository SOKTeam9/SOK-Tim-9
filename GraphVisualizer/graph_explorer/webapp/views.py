















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



























































def reset_graph(request):
    filters.clear()
    return simple_visualizer(request)

def simple_visualizer(request):
    handler = GraphHandler("neo4j://127.0.0.1:7687", "neo4j", "djomlaboss")
    graph_data = handler.get_subgraph(filters)
    visualizer = SimpleVisualizer()
    context = visualizer.get_context(graph_data)
    context["filter_string"] = _applied_filters()
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
 
            single_filter = (attribute, operator, actual_value)
            if single_filter not in filters:
                filters.append(single_filter)
        return simple_visualizer(request)


def apply_filter(request):
     if request.method == "POST":
        filter_attribute = request.POST.get("filter", "").strip()
        filter_relation = request.POST.get("relations", "").strip()
        filter_value = request.POST.get("value", "").strip()

        if filter_attribute != "" and filter_relation != "" and filter_value != "":
            try:
                actual_value = float(filter_value)
            except:
                actual_value = filter_value
            
            single_filter = (filter_attribute, filter_relation, actual_value)
            if single_filter not in filters:
                filters.append(single_filter)
        
        return simple_visualizer(request)
    
def _applied_filters():
    list_strings = []
    for filter in filters:
        list_strings.append("".join(str(x) for x in filter))
    
    filter_string = ",".join(list_strings)
    return filter_string