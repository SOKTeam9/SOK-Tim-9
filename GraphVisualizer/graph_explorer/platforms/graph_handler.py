from neo4j import GraphDatabase
from neo4j.time import Date, DateTime

def serialize_value(value):
    if isinstance(value, (Date, DateTime)):
        return str(value)  # npr. "2025-08-20"
    if isinstance(value, list):
        return [serialize_value(v) for v in value]
    if isinstance(value, dict):
        return {k: serialize_value(v) for k, v in value.items()}
    return value

class GraphHandler:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def get_graph(self):
        # 1. Pribavi sve čvorove
        nodes_query = "MATCH (n:Node) RETURN n"
        links_query = "MATCH (n:Node)-[r]->(m:Node) RETURN n, r, m"

        nodes = {}
        links = []

        with self.driver.session() as session:
            # Čvorovi
            for record in session.run(nodes_query):
                n = record["n"]
                node_id = n.get("id", n.element_id)
                if node_id not in nodes:
                    nodes[node_id] = {
                        "id": node_id,
                        "labels": list(n.labels),
                        "properties": {k: str(v) for k, v in n.items()}
                    }

            # Veze
            for record in session.run(links_query):
                n = record["n"]
                m = record["m"]
                r = record["r"]

                source_id = n.get("id", n.element_id)
                target_id = m.get("id", m.element_id)

                # Dodaj čvor m ako nije već dodat
                if target_id not in nodes:
                    nodes[target_id] = {
                        "id": target_id,
                        "labels": list(m.labels),
                        "properties": {k: str(v) for k, v in m.items()}
                    }

                # Dodaj vezu
                links.append({
                    "source": source_id,
                    "target": target_id,
                    "type": r.type,
                    "properties": {k: str(v) for k, v in r.items()}})

        return {"nodes": list(nodes.values()), "links": links}

    def close(self):
        self.driver.close()


if __name__ == "__main__":
    handler = GraphHandler("neo4j://127.0.0.1:7687", "neo4j", "djomlaboss")
    print(handler.get_graph())
    handler.close()
