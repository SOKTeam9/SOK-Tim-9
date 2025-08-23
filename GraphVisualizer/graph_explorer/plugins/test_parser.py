from neo4j import GraphDatabase
from .data_source_plugin_xml import XmlFileParser
from .data_source_plugin_yaml import YamlFileParser
from .data_source_plugin_json import JSONGraphParser
from pathlib import Path

def run_test():
    uri = "neo4j://127.0.0.1:7687"
    username = "neo4j"
    password = "djomlaboss"

    driver = None
    try:
        driver = GraphDatabase.driver(uri, auth=(username, password))
        driver.verify_connectivity()
        print("Uspešno povezano sa Neo4j bazom.")

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

        # Kreiranje i pokretanje parsera za "users.xml"

        # print("Parsiranje users.xml...")
        # xml_path = Path(__file__).parent / "data_source_plugin_xml" / "users.xml"
        # parser_users = XmlFileParser(str(xml_path), driver, config_users)
        # parser_users.load()
        # print("Parsiranje i uvoz users.xml uspešno završeno!")

        # Kreiranje i pokretanje parsera za "employees.xml"

        # print("\nParsiranje employees.xml...")
        # xml_path2 = Path(__file__).parent / "data_source_plugin_xml" / "employees.xml"
        # parser_employees = XmlFileParser(str(xml_path2), driver, config_employees)
        # parser_employees.load()
        # print("Parsiranje i uvoz employees.xml uspešno završeno!")

        # print("\nParsiranje a.yaml...")
        # yaml_path = Path(__file__).parent / "data_source_plugin_yaml" / "a.yaml"
        # parser_a = YamlFileParser(str(yaml_path), driver)
        # parser_a.load()
        # print("Parsiranje a.yaml uspešno završeno!")

        # print("\nParsiranje test.yaml...")
        # yaml_path = Path(__file__).parent / "data_source_plugin_yaml" / "test.yaml"
        # parser_a = YamlFileParser(str(yaml_path), driver)
        # parser_a.load()
        # print("Parsiranje test.yaml uspešno završeno!")


        print("\nParsiranje countries.json...")
        json_path = Path(__file__).parent / "data_source_plugin_json" / "test.json"
        parser_countries = JSONGraphParser(str(json_path), driver)
        parser_countries.load()
        print("Parsiranje countries.json uspešno završeno!")

        



    except Exception as e:
        print(f"Došlo je do greške: {e}")
    finally:
        if driver:
            driver.close()

if __name__ == "__main__":
    run_test()

    # MATCH (n)
# OPTIONAL MATCH (n)-[r]-()
# RETURN n, r