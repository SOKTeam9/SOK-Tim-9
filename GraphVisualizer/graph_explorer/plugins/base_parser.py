from abc import ABC, abstractmethod

#TEMPLATE METHOD PATTERN
class BaseParser(ABC):
    def __init__(self, file_name, driver, database="neo4j1"):
        self.file_name = file_name
        self.driver = driver
        self.database = database

    def load(self):
        with self.driver.session(database=self.database) as session:
            session.execute_write(self.clear_database)
            
            nodes, relationships = self.parse_data()

            session.execute_write(self.create_nodes, nodes)
            session.execute_write(self.create_relationships, relationships)

    def clear_database(self, tx):
        tx.run("MATCH (n) DETACH DELETE n")

    def create_nodes(self, tx, nodes):
        for node_data in nodes:
            label = node_data.get("label", "Node")
            node_data_for_cypher = {k: v for k, v in node_data.items() if k != "label"}
            cypher_keys = ", ".join(f"{k}: ${k}" for k in node_data_for_cypher.keys())
            tx.run(f"CREATE (:{label} {{ {cypher_keys} }})", **node_data_for_cypher)

    def create_relationships(self, tx, relationships):
        for source_id, target_id, rel_type in relationships:
            rel_type_upper = rel_type.upper().replace(" ", "_")
            query = f"""
                MATCH (a {{id: $source_id}})
                MATCH (b {{id: $target_id}})
                CREATE (a)-[:{rel_type_upper}]->(b)
            """
            tx.run(query, source_id=source_id, target_id=target_id)
    
    @abstractmethod
    def parse_data(self):
        """
        An abstract method for parsing a file and returning nodes and relationships.
Every subclass must implement this method.
        """
        pass