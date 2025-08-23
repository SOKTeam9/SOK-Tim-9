from neo4j import GraphDatabase

import yaml
from ..base_parser import BaseParser

import yaml

class YamlFileParser(BaseParser):
    def __init__(self, file_name, driver):
        super().__init__(file_name, driver)
    
    def parse_data(self):
        nodes = []
        relationships = []
        
        with open(self.file_name, "r") as f:
            data = yaml.safe_load(f)

        all_ids = set()
        group_list = data.values()
        for group in group_list:
            for item in group:
                all_ids.add(item["id"])
        
        for group_name, data_pool in data.items():
            for single_data in data_pool:
                node_data = {}
                
                for key, value in single_data.items():
                    if isinstance(value, list):
                        for item in value:
                            if item in all_ids:
                                relationships.append((single_data["id"], item, key))
                            else:
                                pass
                    elif key not in all_ids:
                        node_data[key] = value

                node_props = {k: v for k, v in single_data.items() if not isinstance(v, list) or (isinstance(v, list) and not any(item in all_ids for item in v))}
                
                node_props["label"] = group_name.capitalize()
                print(node_props)
                nodes.append(node_props)

        return nodes, relationships

#TEST
if __name__ == "__main__":
	uri = "neo4j://127.0.0.1:7687"
	username = "neo4j"
	password = "djomlaboss"

	# Kreiranje drajvera
	driver = GraphDatabase.driver(uri, auth=(username, password))

	parser = YamlFileParser("C:\\Users\\mpetr\\OneDrive\\Desktop\\SOK\\SOK-Tim-9\\GraphVisualizer\\graph_explorer\\plugins\\data-source-plugin-yaml\\test.yaml", driver)
	parser.load()
	# Zatvaranje drajvera
	driver.close()