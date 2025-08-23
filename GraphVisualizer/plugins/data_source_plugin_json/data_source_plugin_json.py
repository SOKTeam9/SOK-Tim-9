import json
from neo4j import GraphDatabase
from datetime import date, timedelta

class JSONGraphParser:
    def __init__(self, key_field="id"):
        self.key_field = key_field

    def parse_json_file(self, json_file):
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        if isinstance(data, dict):
            objects = [{self.key_field: k, **v} for k, v in data.items()]
        elif isinstance(data, list):
            objects = data
        else:
            raise ValueError("JSON file must be list or dict")
        return objects
    
    def flatten_objects(self, obj, parent_id=None, parent_field=None):
        nodes = []
        relationships = []

        if self.key_field not in obj:
            raise ValueError(f"Object does not have key '{self.key_field}': {obj}")

        node_id = obj[self.key_field]
        node_props = {}

        for k, v in obj.items():
            if isinstance(v, dict):
                child_nodes, child_rels = self.flatten_objects(v)
                nodes.extend(child_nodes)
                relationships.extend(child_rels)
                relationships.append((node_id, v.get(self.key_field), k.upper()))
            elif isinstance(v, list):
                for item in v:
                    if isinstance(item, dict):
                        child_nodes, child_rels = self.flatten_objects(item)
                        nodes.extend(child_nodes)
                        relationships.extend(child_rels)
                        relationships.append((node_id, item.get(self.key_field), k.upper()))
                    else:
                        relationships.append((node_id, item, k.upper()))
            else:
                node_props[k] = v

        nodes.append({self.key_field: node_id, **node_props})

        if parent_id and parent_field:
            relationships.append((parent_id, node_id, parent_field.upper()))

        return nodes, relationships
    
    def get_nodes_and_relationships(self, objects):
        all_nodes = []
        all_relationships = []
        for obj in objects:
            nodes, rels = self.flatten_objects(obj)
            all_nodes.extend(nodes)
            all_relationships.extend(rels)

        seen = set()
        unique_nodes = []
        for n in all_nodes:
            nid = n[self.key_field]
            if nid not in seen:
                unique_nodes.append(n)
                seen.add(nid)

        return unique_nodes, all_relationships
    
