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

        if len(filters) == 0:
            return self.get_graph()

        query = "MATCH (n) "
        if len(filters) != 0:
            conditions = []
            for attr, op, val in filters:
                if isinstance(val, str):
                    val_repr = f"'{val}'"
                else:
                    val_repr = str(val)
                conditions.append(f"n.{attr} {op} {val_repr}")
            query += "WHERE " + " AND ".join(conditions)

        query += """
        OPTIONAL MATCH (n)-[r]->(m)
        WHERE """ + " AND ".join([f"m.{attr} {op} {repr(val) if isinstance(val, str) else val}" for attr, op, val in filters]) + """
        RETURN n, r, m
        """


        with self.driver.session() as session:
            results = session.run(query)

            for record in results:
                n = record["n"]
                m = record["m"]
                r = record["r"]

                # Dodaj čvorove u dict (da ne dupliraš)
                nodes[n.id] = {"id": n.id, "labels": list(n.labels), "properties": dict(n)}
                if m != None:
                    nodes[m.id] = {"id": m.id, "labels": list(m.labels), "properties": dict(m)}

                if r != None:
                    # Dodaj vezu
                    edges.append({
                        "id": r.id,
                        "source": n.id,
                        "target": m.id,
                        "type": r.type,
                        "properties": dict(r)
                    })

        return {"nodes": list(nodes.values()), "edges": edges}

if __name__ == "__main__":
    handler = GraphHandler("neo4j://127.0.0.1:7687", "neo4j", "djomlaboss")
    # print(handler.get_graph())
    handler.close()
    # simple = SimpleVisualizer()
    # simple.render(handler.get_graph())