from neo4j import GraphDatabase
import xml.etree.ElementTree as ET
from datetime import datetime
from ..base_parser import BaseParser

import xml.etree.ElementTree as ET
from datetime import datetime

class XmlFileParser(BaseParser):
    def __init__(self, file_name, driver):
        super().__init__(file_name, driver)

    def parse_data(self):
        nodes = []
        relationships = []
        
        try:
            tree = ET.parse(self.file_name)
            root = tree.getroot()
        except ET.ParseError as e:
            print(f"Greška pri parsiranju XML fajla: {e}")
            return [], []

        if not root:
            return [], []
        main_node_tag = root[0].tag
        
        for node_element in root.findall(main_node_tag):
            node_id = node_element.get('id')
            node_data = {"id": node_id}
            
            node_data["label"] = main_node_tag.capitalize()
            
            for child in node_element:
                if len(child) > 0:
                    relationship_name = child.tag.upper().replace(" ", "_")
                    for ref_element in child:
                        target_id = ref_element.get('ref')
                        if target_id:
                            relationships.append((node_id, target_id, relationship_name))
                else:
                    value = child.text
                    if value is not None:
                        try:
                            date_obj = datetime.strptime(value, '%Y-%m-%d').date()
                            node_data[child.tag] = date_obj
                        except ValueError:
                            if value.isdigit():
                                node_data[child.tag] = int(value)
                            elif value.lower() == 'true':
                                node_data[child.tag] = True
                            elif value.lower() == 'false':
                                node_data[child.tag] = False
                            else:
                                node_data[child.tag] = value
            
            nodes.append(node_data)
        
        return nodes, relationships

# TEST
if __name__ == "__main__":
    uri = "neo4j://127.0.0.1:7687"
    username = "neo4j"
    password = "djomlaboss"

    driver = GraphDatabase.driver(uri, auth=(username, password))
    
    # Konfiguracija za fajl "users.xml"
    config_users = {
        'node_tag': 'user',
        'relationship_tag': 'follows',
        'relationship_name': 'follows'
    }
    
    # Konfiguracija za fajl "employees.xml"
    config_employees = {
        'node_tag': 'employee',
        'relationship_tag': 'colleagues_with',
        'relationship_name': 'colleagues_with'
    }
    
    print("Parsiranje users.xml...")
    parser_users = XmlFileParser("users.xml", driver, config_users)

    # print("Parsiranje employees.xml...")
    # parser_employees = XmlFileParser("employees.xml", driver, config_employees)
    
    driver.close()

# MATCH (n)
# OPTIONAL MATCH (n)-[r]-()
# RETURN n, r