from ..base_parser import BaseParser
import json

class JSONGraphParser(BaseParser):
    def __init__(self, file_name, driver, key_field="id", node_label="Node"):
        super().__init__(file_name, driver)
        self.key_field = key_field
        self.node_label = node_label

    def parse_data(self):
        try:
            with open(self.file_name, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except FileNotFoundError:
            raise ValueError(f"File {self.file_name} not found")
            
        if isinstance(data, dict):
            objects = [{self.key_field: k, **v} for k, v in data.items()]
        elif isinstance(data, list):
            objects = data
        else:
            raise ValueError("JSON file must be list or dict")
        
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
                n["label"] = self.node_label
                unique_nodes.append(n)
                seen.add(nid)

        return unique_nodes, all_relationships

    def flatten_objects(self, obj, parent_id=None, parent_field=None):
        nodes = []
        relationships = []

        if self.key_field not in obj:
            raise ValueError(f"Object does not have key '{self.key_field}': {obj}")

        node_id = obj[self.key_field]
        node_props = {}

        for k, v in obj.items():
            if k == self.key_field:
                continue

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