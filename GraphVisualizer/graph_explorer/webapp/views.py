
from django.apps import apps
from django.shortcuts import render, redirect
from django.http import JsonResponse
from platforms.graph_handler import GraphHandler
from neo4j.time import Date, DateTime
from plugins.visualizer_block.block_visualizer import BlockVisualizer
import json
import datetime
from plugins.factory import ParserFactory, VisualizerFactory
from plugins.visualizer_simple.simple_visualizer import SimpleVisualizer
from plugins.data_source_plugin_yaml.yaml_data_source_plugin import YamlFileParser
from neo4j import GraphDatabase
import os
import tempfile

filters = []

# URI obavezno promeni u "bolt://..." umesto neo4j://, jer ti je single instance
handler = GraphHandler("neo4j://127.0.0.1:7687", "neo4j", "djomlaboss")

current_view = "simple"

def index(request):
    return render(request, 'index.html', {'title': 'Index'})

def reset_graph(request):
    filters.clear()
    if current_view == "simple":
        return simple_visualizer(request)
    else:
        return block_view(request)

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

def block_view(request, file_name=None):
    global current_view
    current_view = "block"
    handler = GraphHandler("neo4j://127.0.0.1:7687", "neo4j", "djomlaboss")
    graph_data = handler.get_subgraph(filters)  # vraća nodes + links

    visualizer = VisualizerFactory.create_visualizer("block", graph_data)
    html = visualizer.render()

    string_filters = _applied_filters()

    return render(request, "block-template.html", {"graph_json": graph_data, "filter_string": string_filters, "selected_file_name": file_name})

def simple_visualizer(request, file_name=None):
    global current_view
    current_view = "simple"
    handler = GraphHandler("neo4j://127.0.0.1:7687", "neo4j", "djomlaboss")
    graph_data = handler.get_subgraph(filters)

    visualizer = VisualizerFactory.create_visualizer("simple")
    context = visualizer.get_context(graph_data)

    context["filter_string"] = _applied_filters()
    context["selected_file_name"] = file_name
    return render(request, "simple_template.html", context)

def load_file(request=None):
    selected_file_name = None

    if request is not None:
        if request.method == "POST":
            uploaded_file = request.FILES.get("load_file")
            if uploaded_file:
                selected_file_name = uploaded_file.name
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

            parser = ParserFactory.create_parser(tmp_path, driver, file_type)
            parser.load()
            # Zatvaranje drajvera
            driver.close()

            # Možeš odmah obrisati privremeni fajl
            os.remove(tmp_path)
    
    if current_view == "simple":
        return simple_visualizer(request, selected_file_name)
    else:
        return block_view(request, selected_file_name)

def make_search(request=None):
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
        if current_view == "simple":
            return simple_visualizer(request)
        else:
            return block_view(request)


def apply_filter(request=None):
    if request is not None:
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
            
    if current_view == "simple":
        return simple_visualizer(request)
    else:
        return block_view(request)
    
def _applied_filters():
    list_strings = []
    list_strings_to_file = []
    for filter in filters:
        list_strings.append("".join(str(x) for x in filter))
        list_strings_to_file.append("~".join(str(x) for x in filter))
    
    filter_string = ",".join(list_strings)
    # filter_string_to_file = ",".join(list_strings_to_file)
    # with open("session.txt", "w+") as f:
    #     f.write(filter_string_to_file + "\n")
    #     f.write(current_view)

    return list_strings

def filter_remove(request):
    selected_filter = request.GET.get("filter")
    for single_filter in filters:
        merged = "".join(str(x) for x in single_filter)
        if selected_filter == merged:
            filters.remove(single_filter)
            break
    if current_view == "simple":
        return simple_visualizer(request)
    else:
        return block_view(request)
