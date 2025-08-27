
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
from django.views.decorators.csrf import csrf_exempt

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
    if workspaces[str(ws_id)]["view_type"] == "simple":
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
    print("GRAPH DATA: ", graph_data)

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
            attribute = search_query.split("~")[0]
            operator = search_query.split("~")[1]
            value = search_query.split("~")[2]

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

@csrf_exempt
def create_node(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            node_id = data.get("id")
            properties = data.get("properties")

            if not node_id or not properties:
                return JsonResponse({"status": "error", "message": "ID and properties are required."}, status=400)

            handler = GraphHandler("neo4j://127.0.0.1:7687", "neo4j", "djomlaboss")
            created = handler.create_node(node_id, properties, "neo4j"+workspaces['active'])
            handler.close()

            if created:
                return JsonResponse({"status": "success", "message": f"Node with ID '{node_id}' created successfully."}, status=201)
            else:
                return JsonResponse({"status": "error", "message": "Failed to create node."}, status=500)

        except json.JSONDecodeError:
            return JsonResponse({"status": "error", "message": "Invalid JSON format."}, status=400)
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=500)
    
    return JsonResponse({"status": "error", "message": "Method not allowed."}, status=405)

@csrf_exempt
def edit_node(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            node_id = data.get("id")
            properties = data.get("properties")

            if not node_id or not properties:
                return JsonResponse({"status": "error", "message": "ID and properties are required."}, status=400)

            updated = handler.update_node(node_id, properties)
            handler.close()

            if updated:
                return JsonResponse({"status": "success", "message": f"Node with ID '{node_id}' updated successfully."}, status=200)
            else:
                return JsonResponse({"status": "error", "message": f"Node with ID '{node_id}' not found."}, status=404)

        except json.JSONDecodeError:
            return JsonResponse({"status": "error", "message": "Invalid JSON format."}, status=400)
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=500)
    
    return JsonResponse({"status": "error", "message": "Method not allowed."}, status=405)

@csrf_exempt
def delete_node(request):
    print("kjhgfd")
    print(request)
    if request.method == "DELETE":
        try:
            data = json.loads(request.body)
            print("****************")
            print("data: ",data)
            node_id = data.get("id")
            print("node id: ", node_id)
            print("**************")
            if not node_id:
                return JsonResponse({"status": "error", "message": "ID je obavezan."}, status=400)

            deleted = handler.delete_node(node_id)
            handler.close()

            if deleted:
                return JsonResponse({"status": "success", "message": f"Čvor sa ID-jem '{node_id}' je uspešno obrisan."}, status=200)
            else:
                return JsonResponse({"status": "error", "message": f"Čvor sa ID-jem '{node_id}' ne postoji."}, status=404)

        except ValueError as ve:
            return JsonResponse({"status": "error", "message": str(ve)}, status=400)
        except json.JSONDecodeError:
            return JsonResponse({"status": "error", "message": "Nevažeći JSON format."}, status=400)
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=500)
    
    return JsonResponse({"status": "error", "message": "Metoda nije dozvoljena."}, status=405)

@csrf_exempt
def create_edge(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            rel_type = data.get("type")
            source_id = data.get("source_id")
            target_id = data.get("target_id")

            if not all([rel_type, source_id, target_id]):
                return JsonResponse({"status": "error", "message": "Relacija, početni i krajnji čvor su obavezni."}, status=400)

            created = handler.create_relationship(source_id, target_id, rel_type)
            handler.close()

            if created:
                return JsonResponse({"status": "success", "message": f"Relacija '{rel_type}' uspešno kreirana između čvorova '{source_id}' i '{target_id}'."}, status=201)
            else:
                return JsonResponse({"status": "error", "message": "Neuspešno kreiranje relacije. Proverite da li početni i krajnji čvorovi postoje."}, status=404)

        except json.JSONDecodeError:
            return JsonResponse({"status": "error", "message": "Neispravan JSON format."}, status=400)
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=500)
    
    return JsonResponse({"status": "error", "message": "Metoda nije dozvoljena."}, status=405)

@csrf_exempt
def edit_edge(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            new_rel_type = data.get("type")
            source_id = data.get("source_id")
            target_id = data.get("target_id")

            if not all([new_rel_type, source_id, target_id]):
                return JsonResponse({"status": "error", "message": "Novi tip relacije, početni i krajnji čvor su obavezni."}, status=400)

            edited = handler.edit_relationship(source_id, target_id, new_rel_type)
            handler.close()

            if edited:
                return JsonResponse({"status": "success", "message": f"Relacija između '{source_id}' i '{target_id}' uspešno ažurirana na '{new_rel_type}'."}, status=200)
            else:
                return JsonResponse({"status": "error", "message": "Neuspešno uređivanje relacije. Proverite da li relacija postoji."}, status=404)

        except ValueError as ve:
            return JsonResponse({"status": "error", "message": str(ve)}, status=400)
        except json.JSONDecodeError:
            return JsonResponse({"status": "error", "message": "Neispravan JSON format."}, status=400)
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=500)
    
    return JsonResponse({"status": "error", "message": "Metoda nije dozvoljena."}, status=405)

@csrf_exempt
def delete_edge(request):
    if request.method == "DELETE":
        try:
            data = json.loads(request.body)
            source_id = data.get("source_id")
            target_id = data.get("target_id")

            if not all([source_id, target_id]):
                return JsonResponse({"status": "error", "message": "Početni i krajnji čvor su obavezni."}, status=400)

            deleted = handler.delete_relationship(source_id, target_id)
            handler.close()

            if deleted:
                return JsonResponse({"status": "success", "message": f"Grana između čvorova '{source_id}' i '{target_id}' je uspešno obrisana."}, status=200)
            else:
                return JsonResponse({"status": "error", "message": f"Neuspešno brisanje. Proverite da li grana između '{source_id}' i '{target_id}' postoji."}, status=404)

        except json.JSONDecodeError:
            return JsonResponse({"status": "error", "message": "Neispravan JSON format."}, status=400)
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=500)
    
    return JsonResponse({"status": "error", "message": "Metoda nije dozvoljena."}, status=405)

def cli_search(request):
    print("RADI PREKO CLI SEARCH")
    if request.method == "POST":
        query = request.POST.get("query", "").strip()
        cur_ws = 'neo4j'+workspaces['active']
        if workspaces[workspaces['active']]['view_type']=="simple":
            print("QUERY: ", query)
            graph_data = handler.get_search_subgraph(workspaces[workspaces['active']]['filters'],query, cur_ws)
            print(graph_data)
            print("lennL ", len(graph_data['nodes']))

            visualizer = VisualizerFactory.create_visualizer("simple")
            context = visualizer.get_context(graph_data)
            context["filter_string"] = _applied_filters(int(workspaces['active']))
            context["selected_file_name"] = workspaces[workspaces['active']]["selected_file"]
            context["ws_id"] = int(workspaces['active'])
            write_config()
            return render(request, "simple_template.html", context)
        else:

            graph_data = handler.get_search_subgraph(workspaces[workspaces['active']]['filters'],query, cur_ws)

            visualizer = VisualizerFactory.create_visualizer("block")
            html = visualizer.render(graph_data)

            string_filters = _applied_filters(int(workspaces['active']))
            write_config()
            return render(request, "block-template.html", {"graph_json": graph_data, "filter_string": string_filters, "selected_file_name": workspaces[workspaces['active']]["selected_file"], "ws_id": int(workspaces['active'])})
        
def clear_database(request, ws_id=1):
    if request.method == "POST":
        workspaces[str(ws_id)]['filters'].clear()
        workspaces[str(ws_id)]['selected_file'] = "No file selected"
        write_config()
        print("BRISANJE BAZE")
        if current_view=="simple":
            graph_data = handler.delete_and_get_empty_graph("neo4j"+str(ws_id))
            print(graph_data)
            print("lennL ", len(graph_data['nodes']))

            visualizer = VisualizerFactory.create_visualizer("simple")
            context = visualizer.get_context(graph_data)
            context["filter_string"] = _applied_filters(ws_id)
            context["selected_file_name"] = workspaces[str(ws_id)]["selected_file"]
            context["ws_id"] = ws_id
            return render(request, "simple_template.html", context)
        else:
            graph_data = handler.delete_and_get_empty_graph("neo4j"+str(ws_id))

            visualizer = VisualizerFactory.create_visualizer("block")
            html = visualizer.render(graph_data)

            string_filters = _applied_filters(ws_id)
            return render(request, "block-template.html", {"graph_json": graph_data, "filter_string": string_filters, "selected_file_name": workspaces[str(ws_id)]["selected_file"], "ws_id": ws_id})
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
