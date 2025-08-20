from data_source_plugin_json import JSONGraphParser
from neo4j import GraphDatabase



class Neo4jGraphCreator:
    def __init__(self, uri="neo4j://127.0.0.1:7687", user="neo4j", password="djomlaboss", node_label="Node", key_field="id"):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        self.node_label = node_label
        self.key_field = key_field

    def close(self):
        self.driver.close()

    def clear_database(self):
        with self.driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")

    def create_nodes(self, nodes):
        with self.driver.session() as session:
            for node in nodes:
                session.run(
                    f"MERGE (n:{self.node_label} {{ {self.key_field}: $key }}) SET n += $props",
                    key=node[self.key_field],
                    props=node
                )

    def create_relationships(self, relationships):
        with self.driver.session() as session:
            for source, target, rel_type in relationships:
                if not isinstance(target, (str, int)):
                    continue
                session.run(
                    f"""
                    MATCH (a:{self.node_label} {{ {self.key_field}: $source }})
                    MATCH (b:{self.node_label} {{ {self.key_field}: $target }})
                    MERGE (a)-[r:{rel_type}]->(b)
                    """,
                    source=source,
                    target=target
                )


#TEST
if __name__ == "__main__":
   
    parser = JSONGraphParser(key_field="id")
    objects = parser.parse_json_file(r"C:\Users\Petar\Desktop\countries.json")
    nodes, relationships = parser.get_nodes_and_relationships(objects)

    creator = Neo4jGraphCreator(node_label="Country", key_field="id")
    creator.clear_database()
    creator.create_nodes(nodes)
    creator.create_relationships(relationships)
    creator.close()

    print("✅ Graf iz JSON fajla uspešno kreiran.")
    