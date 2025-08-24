from neo4j import GraphDatabase

class GraphHandler:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def get_graph(self):
        query = """
        MATCH (n)-[r]->(m)
        RETURN n, r, m
        """
        nodes = {}
        edges = []

        with self.driver.session() as session:
            results = session.run(query)

            for record in results:
                n = record["n"]
                m = record["m"]
                r = record["r"]

                # Dodaj čvorove u dict (da ne dupliraš)
                nodes[n.id] = {"id": n.id, "labels": list(n.labels), "properties": dict(n)}
                nodes[m.id] = {"id": m.id, "labels": list(m.labels), "properties": dict(m)}

                # Dodaj vezu
                edges.append({
                    "id": r.id,
                    "source": n.id,
                    "target": m.id,
                    "type": r.type,
                    "properties": dict(r)
                })

        return {"nodes": list(nodes.values()), "edges": edges}
    



















    
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
    # print(handler.get_graph())
    handler.close()
    # simple = SimpleVisualizer()
    # simple.render(handler.get_graph())