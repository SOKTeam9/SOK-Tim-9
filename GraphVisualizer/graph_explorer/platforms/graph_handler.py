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

# class GraphHandler:
#     def __init__(self, uri, user, password):
#         self.driver = GraphDatabase.driver(uri, auth=(user, password))

#     def get_graph(self):
#             query = """
#             MATCH (n)-[r]->(m)
#             RETURN n, r, m
#             """
#             nodes = {}
#             edges = []

#             with self.driver.session() as session:
#                 results = session.run(query)

#                 for record in results:
#                     n = record["n"]
#                     m = record["m"]
#                     r = record["r"]

#                     # Dodaj čvorove u dict (da ne dupliraš)
#                     nodes[n.id] = {"id": n.id, "labels": list(n.labels), "properties": dict(n)}
#                     nodes[m.id] = {"id": m.id, "labels": list(m.labels), "properties": dict(m)}

#                     # Dodaj vezu
#                     edges.append({
#                         "id": r.id,
#                         "source": n.id,
#                         "target": m.id,
#                         "type": r.type,
#                         "properties": dict(r)
#                     })

#             return {"nodes": list(nodes.values()), "links": edges}

#     def close(self):
#         self.driver.close()

#     def get_subgraph(self, filters):
#         nodes = {}
#         edges = []

#         if not filters:
#             return self.get_graph()

#         with self.driver.session() as session:
#             subgraph_ids = set()

#             # Prođi kroz sve filtere
#             for i, (attr, op, val) in enumerate(filters):
#                 val_repr = f"'{val}'" if isinstance(val, str) else str(val)

#                 if i == 0:
#                     # Prvi filter – uzmi sve čvorove koji zadovoljavaju filter
#                     query_nodes = f"""
#                     MATCH (n)
#                     WHERE n.{attr} {op} {val_repr}
#                     RETURN n
#                     """
#                 else:
#                     # Sledeći filteri – uzmi samo čvorove koji su već u podgrafu
#                     query_nodes = f"""
#                     MATCH (n)
#                     WHERE n.{attr} {op} {val_repr} AND id(n) IN {list(subgraph_ids)}
#                     RETURN n
#                     """

#                 results = session.run(query_nodes)

#                 # Ažuriraj čvorove
#                 new_nodes = {}
#                 subgraph_ids = set()
#                 for record in results:
#                     n = record["n"]
#                     new_nodes[n.id] = {
#                         "id": n.id,
#                         "labels": list(n.labels),
#                         "properties": dict(n)
#                     }
#                     subgraph_ids.add(n.id)

#                 nodes = new_nodes  # samo čvorovi koji prežive filter

#                 # Uzmi veze između preživelih čvorova
#                 if subgraph_ids:
#                     query_edges = f"""
#                     MATCH (n)-[r]->(m)
#                     WHERE id(n) IN {list(subgraph_ids)} AND id(m) IN {list(subgraph_ids)}
#                     RETURN r, n, m
#                     """
#                     results = session.run(query_edges)
#                     edges = []
#                     for record in results:
#                         r = record["r"]
#                         n = record["n"]
#                         m = record["m"]
#                         edges.append({
#                             "id": r.id,
#                             "source": r.start_node.id,
#                             "target": r.end_node.id,
#                             "type": r.type,
#                             "properties": dict(r)
#                         })
#                 else:
#                     edges = []

#         return {"nodes": list(nodes.values()), "links": edges}

class GraphHandler:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def get_graph(self, database="neo4j"):
        query = """
        MATCH (n)-[r]->(m)
        RETURN n, r, m
        """
        nodes = {}
        edges = []

        with self.driver.session(database=database) as session:
            results = session.run(query)

            for record in results:
                n = record["n"]
                m = record["m"]
                r = record["r"]

                nodes[n.id] = {"id": n.id, "labels": list(n.labels), "properties": dict(n)}
                nodes[m.id] = {"id": m.id, "labels": list(m.labels), "properties": dict(m)}

                edges.append({
                    "id": r.id,
                    "source": n.id,
                    "target": m.id,
                    "type": r.type,
                    "properties": dict(r)
                })

        return {"nodes": list(nodes.values()), "links": edges}

    def get_subgraph(self, filters, database="neo4j"):
        nodes = {}
        edges = []

        if not filters:
            return self.get_graph(database=database)

        with self.driver.session(database=database) as session:
            subgraph_ids = set()

            for i, (attr, op, val) in enumerate(filters):
                val_repr = f"'{val}'" if isinstance(val, str) else str(val)

                if i == 0:
                    query_nodes = f"""
                    MATCH (n)
                    WHERE n.{attr} {op} {val_repr}
                    RETURN n
                    """
                else:
                    query_nodes = f"""
                    MATCH (n)
                    WHERE n.{attr} {op} {val_repr} AND id(n) IN {list(subgraph_ids)}
                    RETURN n
                    """

                results = session.run(query_nodes)

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

                nodes = new_nodes

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
                        edges.append({
                            "id": r.id,
                            "source": r.start_node.id,
                            "target": r.end_node.id,
                            "type": r.type,
                            "properties": dict(r)
                        })
                else:
                    edges = []

        return {"nodes": list(nodes.values()), "links": edges}

    def close(self):
        self.driver.close()

if __name__ == "__main__":
    # handler = GraphHandler("neo4j://127.0.0.1:7687", "neo4j", "djomlaboss")
    # print(handler.get_graph())
    # handler.close()
    handler = GraphHandler("neo4j://127.0.0.1:7687", "neo4j", "djomlaboss")

    # iz default "neo4j" baze
    print(handler.get_graph())
    print(" ")
    print(" ")
    print(" ")
    print(" ")
    print(" ")
    print("sledeca")
    # iz druge baze, npr. "test"
    print(handler.get_graph(database="neo4j2"))

    handler.close()