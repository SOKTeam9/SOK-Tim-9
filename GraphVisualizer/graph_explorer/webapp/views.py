
from django.apps import apps
from django.shortcuts import render, redirect
from django.http import JsonResponse
from platforms.graph_handler import GraphHandler
from neo4j.time import Date, DateTime
import json
import datetime
from plugins import ParserFactory, VisualizerFactory
from neo4j import GraphDatabase
import os
import tempfile

filters = []

# URI obavezno promeni u "bolt://..." umesto neo4j://, jer ti je single instance
handler = GraphHandler("neo4j://127.0.0.1:7687", "neo4j", "djomlaboss")

current_view = "simple"

workspaces = {
    "active" : "1",
    "1": {
        "view_type": "simple",
        "filters": [],
        "selected_file": "No file selected"
    },
    "2": {
        "view_type": "simple",
        "filters": [],
        "selected_file": "No file selected"
    },
    "3": {
        "view_type": "simple",
        "filters": [],
        "selected_file": "No file selected"
    },
    "4": {
        "view_type": "simple",
        "filters": [],
        "selected_file": "No file selected"
    },
    "5": {
        "view_type": "simple",
        "filters": [],
        "selected_file": "No file selected"
    },
}

current_workspace = 1

def index(request):
    return render(request, 'index.html', {'title': 'Index', 'ws_id': 1, 'selected_file_name': workspaces["1"]["selected_file"]})

def reset_graph(request, ws_id):
    workspaces[str(ws_id)]["filters"].clear()
    write_config()
    if workspaces[str(ws_id)]["filters"] == "simple":
        return simple_visualizer(request, ws_id=ws_id)
    else:
        return block_view(request, ws_id=ws_id)

class Neo4jJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        # Neo4j datumi
        if isinstance(obj, (Date, DateTime)):
            return str(obj)  # '2025-08-20' ili '2025-08-20 14:55:00'

        # Python datumi
        if isinstance(obj, (datetime.date, datetime.datetime)):
            return obj.isoformat()  # '2025-08-20T14:55:00'

        return super().default(obj)


def graph_block_data(request, ws_id):
    handler = GraphHandler("neo4j://127.0.0.1:7687", "neo4j", "djomlaboss")
    return JsonResponse(
    handler.get_graph("neo4j" + str(ws_id)),
    safe=False,
    encoder=Neo4jJSONEncoder)

def block_view(request, file_name=None, ws_id=1):
    workspaces[str(ws_id)]["view_type"] = "block"
    handler = GraphHandler("neo4j://127.0.0.1:7687", "neo4j", "djomlaboss")
    graph_data = handler.get_subgraph(workspaces[str(ws_id)]["filters"], "neo4j" + str(ws_id))  # vraća nodes + links

    visualizer = VisualizerFactory.create_visualizer("block", graph_data)
    html = visualizer.visualize(graph_data)

    string_filters = _applied_filters(ws_id)

    write_config()
    return render(request, "block-template.html", {"graph_json": graph_data, "filter_string": string_filters, "selected_file_name": workspaces[str(ws_id)]["selected_file"], "ws_id": ws_id})

def simple_visualizer(request, file_name=None, ws_id=1):
    workspaces[str(ws_id)]["view_type"] = "simple"
    handler = GraphHandler("neo4j://127.0.0.1:7687", "neo4j", "djomlaboss")
    graph_data = handler.get_subgraph(workspaces[str(ws_id)]["filters"], "neo4j" + str(ws_id))

    visualizer = VisualizerFactory.create_visualizer("simple")

    context = visualizer.visualize(graph_data)

    context["filter_string"] = _applied_filters(ws_id)
    context["selected_file_name"] = workspaces[str(ws_id)]["selected_file"]
    context["ws_id"] = ws_id
    write_config()
    return render(request, "simple_template.html", context)

def workspace_switch(request, ws_id=1):
    workspaces["active"] = str(ws_id)
    write_config()
    if workspaces[str(ws_id)]["view_type"] == "simple":
        return simple_visualizer(request, ws_id=ws_id)
    else:
        return block_view(request, ws_id=ws_id)

def load_file(request=None, ws_id=1):
    selected_file_name = None

    if request is not None:
        if request.method == "POST":
            uploaded_file = request.FILES.get("load_file")
            if uploaded_file:
                selected_file_name = uploaded_file.name
                workspaces[str(ws_id)]["selected_file"] = selected_file_name
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

            parser = ParserFactory.create_parser(tmp_path, driver, file_type, "neo4j" + str(ws_id))
            parser.load()

            # Zatvaranje drajvera
            driver.close()

            # Možeš odmah obrisati privremeni fajl
            os.remove(tmp_path)
    
    write_config()
    if workspaces[str(ws_id)]["view_type"] == "simple":
        return simple_visualizer(request, selected_file_name, ws_id)
    else:
        return block_view(request, selected_file_name, ws_id)

def make_search(request=None, ws_id=1):
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
            if single_filter not in workspaces[str(ws_id)]["filters"]:
                workspaces[str(ws_id)]["filters"].append(single_filter)

        write_config()
        if workspaces[str(ws_id)]["view_type"] == "simple":
            return simple_visualizer(request, ws_id=ws_id)
        else:
            return block_view(request, ws_id=ws_id)


def apply_filter(request=None, ws_id=1):
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
                if single_filter not in workspaces[str(ws_id)]["filters"]:
                    workspaces[str(ws_id)]["filters"].append(single_filter)
    
    write_config()  
    if workspaces[str(ws_id)]["view_type"] == "simple":
        return simple_visualizer(request, ws_id=ws_id)
    else:
        return block_view(request, ws_id=ws_id)
    
def _applied_filters(ws_id):
    list_strings = []
    for filter in workspaces[str(ws_id)]["filters"]:
        list_strings.append("".join(str(x) for x in filter))
    
    return list_strings

def filter_remove(request, ws_id=1):
    selected_filter = request.GET.get("filter")
    for single_filter in workspaces[str(ws_id)]["filters"]:
        merged = "".join(str(x) for x in single_filter)
        if selected_filter == merged:
            workspaces[str(ws_id)]["filters"].remove(single_filter)
            break
    
    write_config()
    if workspaces[str(ws_id)]["view_type"] == "simple":
        return simple_visualizer(request, ws_id=ws_id)
    else:
        return block_view(request, ws_id=ws_id)

def load_config():
    with open("AppConfig.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    return data

def write_config():
    with open("AppConfig.json", "w", encoding="utf-8") as f:
        json.dump(workspaces, f, indent=4, ensure_ascii=False)

def redirect(request):
    global workspaces
    workspaces = load_config()
    return workspace_switch(request, int(workspaces["active"]))