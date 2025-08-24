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

    def get_subgraph(self, filters):
        nodes = {}
        edges = []

        if not filters:
            return self.get_graph()

        with self.driver.session() as session:
            subgraph_ids = set()

            # Prođi kroz sve filtere
            for i, (attr, op, val) in enumerate(filters):
                val_repr = f"'{val}'" if isinstance(val, str) else str(val)

                if i == 0:
                    # Prvi filter – uzmi sve čvorove koji zadovoljavaju filter
                    query_nodes = f"""
                    MATCH (n)
                    WHERE n.{attr} {op} {val_repr}
                    RETURN n
                    """
                else:
                    # Sledeći filteri – uzmi samo čvorove koji su već u podgrafu
                    query_nodes = f"""
                    MATCH (n)
                    WHERE n.{attr} {op} {val_repr} AND id(n) IN {list(subgraph_ids)}
                    RETURN n
                    """

                results = session.run(query_nodes)

                # Ažuriraj čvorove
                new_nodes = {}
                subgraph_ids = set()
                for record in results:
                    n = record["n"]
                    new_nodes[n.id] = {
                        "id": n.id,
                        "labels": list(n.labels),
                        "properties": dict(n)
                    }
                    subgraph_ids.add(n.id)

                nodes = new_nodes  # samo čvorovi koji prežive filter

                # Uzmi veze između preživelih čvorova
                if subgraph_ids:
                    query_edges = f"""
                    MATCH (n)-[r]->(m)
                    WHERE id(n) IN {list(subgraph_ids)} AND id(m) IN {list(subgraph_ids)}
                    RETURN r, n, m
                    """
                    results = session.run(query_edges)
                    edges = []
                    for record in results:
                        r = record["r"]
                        n = record["n"]
                        m = record["m"]
                        edges.append({
                            "id": r.id,
                            "source": r.start_node.id,
                            "target": r.end_node.id,
                            "type": r.type,
                            "properties": dict(r)
                        })
                else:
                    edges = []

        return {"nodes": list(nodes.values()), "edges": edges}

if __name__ == "__main__":
    handler = GraphHandler("neo4j://127.0.0.1:7687", "neo4j", "djomlaboss")
    print(handler.get_graph())
    handler.close()
