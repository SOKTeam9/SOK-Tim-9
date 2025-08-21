from neo4j import GraphDatabase
import xml.etree.ElementTree as ET
from datetime import datetime

class XmlFileParser:
    def __init__(self, file_name, driver, config):
        self.file_name = file_name
        self.root = None
        self.driver = driver
        self.relationships = []
        self.config = config
        self.load()

    def load(self):
        try:
            tree = ET.parse(self.file_name)
            self.root = tree.getroot()
        except ET.ParseError as e:
            print(f"Greška pri parsiranju XML fajla: {e}")
            return
        
        with self.driver.session() as session:
            session.execute_write(self.clear_database)
            session.execute_write(self.create_nodes_and_relationships)

    def clear_database(self, tx):
        tx.run("MATCH (n) DETACH DELETE n")

    def create_nodes_and_relationships(self, tx):
        node_tag_name = self.config['node_tag'].capitalize()
        relationship_tag = self.config['relationship_tag']
        relationship_name = self.config['relationship_name'].upper()

        for node_element in self.root.findall(self.config['node_tag']):
            node_id = node_element.get('id')
            node_data = {"id": node_id}
            
            for child in node_element:
                if child.tag == relationship_tag:
                    for ref_element in child:
                        target_id = ref_element.get('ref')
                        if target_id:
                            self.relationships.append((node_id, target_id, relationship_name))
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
            
            props_str = ", ".join([f"{k}: ${k}" for k in node_data])
            query = f"CREATE (n:{node_tag_name} {{ {props_str} }})"
            tx.run(query, **node_data)
            
        for source_id, target_id, rel_type in self.relationships:
            query = f"""
            MATCH (a:{node_tag_name} {{id: $source_id}})
            MATCH (b:{node_tag_name} {{id: $target_id}})
            CREATE (a)-[:{rel_type}]->(b)
            """
            tx.run(query, source_id=source_id, target_id=target_id)

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