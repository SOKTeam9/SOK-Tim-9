from neo4j import GraphDatabase
from neo4j.time import Date, DateTime
from datetime import date, datetime
from neo4j.exceptions import ClientError

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

    # def serialize_value(self,value):
    #     if isinstance(value, (date, datetime, Date)):
    #         return value.isoformat()  # "2025-08-24" ili "2025-08-24T14:35:12"
    #     if isinstance(value, bool):
    #         return bool(value)  # reši True/False problem
    #     return value

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

                nodes[n.id] = {"id": n.id, "labels": list(n.labels), "properties": serialize_value(dict(n))}
                nodes[m.id] = {"id": m.id, "labels": list(m.labels), "properties": serialize_value(dict(m))}

                edges.append({
                    "id": r.id,
                    "source": n.id,
                    "target": m.id,
                    "type": r.type,
                    "properties": serialize_value(dict(r))
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

    def create_node(self, node_id, properties):
        with self.driver.session() as session:
            query = (
                "CREATE (n {id: $id}) "
                "SET n += $properties "
                "RETURN n"
            )
            result = session.run(query, id=node_id, properties=properties)
            return result.single() is not None
        
    def update_node(self, node_id, properties):
        with self.driver.session() as session:
            query = (
                "MATCH (n {id: $id}) "
                "SET n += $properties "
                "RETURN n"
            )            
            result = session.run(query, id=node_id, properties=properties)
            return result.single() is not None
        
    def delete_node(self, node_id):
        with self.driver.session() as session:
            try:
                query = (
                    "MATCH (n {id: $id}) "
                    "DELETE n"
                )
                result = session.run(query, id=node_id)
                
                return result.consume().counters.nodes_deleted > 0
            except Exception as e:
                if "Cannot delete node" in str(e):
                    raise ValueError(f"Čvor sa ID-jem '{node_id}' je povezan sa drugim čvorovima i ne može biti obrisan.")
                else:
                    raise e
                
    def create_relationship(self, source_id, target_id, rel_type):
            with self.driver.session() as session:
                try:
                    rel_type_upper = rel_type.upper().replace(" ", "_")
                    
                    query = f"""
                        MATCH (a {{id: $source_id}})
                        MATCH (b {{id: $target_id}})
                        CREATE (a)-[:{rel_type_upper}]->(b)
                    """
                    
                    result = session.run(query, source_id=source_id, target_id=target_id)
                    
                    return result.consume().counters.relationships_created > 0
                except Exception as e:
                    print(f"Neo4j error: {e}")
                    return False
                
    def edit_relationship(self, source_id, target_id, new_rel_type):
        with self.driver.session() as session:
            try:
                match_query = (
                    "MATCH (a {id: $source_id})-[r]->(b {id: $target_id}) "
                    "RETURN type(r) AS old_type"
                )
                result = session.run(match_query, source_id=source_id, target_id=target_id)
                old_type_record = result.single()

                if not old_type_record:
                    raise ValueError(f"Relacija između čvorova '{source_id}' i '{target_id}' ne postoji.")
                
                old_type = old_type_record["old_type"]
                
                update_query = f"""
                    MATCH (a {{id: $source_id}})-[r]->(b {{id: $target_id}})
                    DELETE r
                    CREATE (a)-[:{new_rel_type.upper().replace(" ", "_")}]->(b)
                """

                update_result = session.run(update_query, source_id=source_id, target_id=target_id)
                
                return update_result.consume().counters.relationships_created > 0
            except Exception as e:
                if "ValueError" in str(e):
                    raise e
                else:
                    print(f"Neo4j error: {e}")
                    raise Exception(f"Neuspešno uređivanje relacije. Detalji: {str(e)}")
                
    def delete_relationship(self, source_id, target_id):
        with self.driver.session() as session:
            try:
                query = f"""
                    MATCH (a {{id: $source_id}})-[r]->(b {{id: $target_id}})
                    DELETE r
                """
                
                result = session.run(query, source_id=source_id, target_id=target_id)
                
                return result.consume().counters.relationships_deleted > 0
            except Exception as e:
                print(f"Neo4j error: {e}")
                return False
            
    def get_search_subgraph(self, filters=None, search_query=None, database="neo4j"):
       
        filters = filters or []

        if not filters and not search_query:
            return self.get_graph(database=database)

        with self.driver.session(database=database) as session:
            conditions = []
            params = {}

            if search_query:
               
                search_condition = """
                (
                ANY(key IN keys(n) WHERE toLower(key) CONTAINS toLower($search_query))
                OR
                ANY(val IN [k IN keys(n) | toString(n[k])] WHERE toLower(val) CONTAINS toLower($search_query))
                )
                """
                conditions.append(search_condition)
                params['search_query'] = search_query

            for i, (attr, op, val) in enumerate(filters):
                param_name = f"filter_val_{i}"
                conditions.append(f"n.`{attr}` {op} ${param_name}")
                params[param_name] = val

           
            where_clause = " AND ".join(conditions)
            query_nodes = f"MATCH (n) WHERE {where_clause} RETURN n"

            results_nodes = session.run(query_nodes, **params)

            nodes = {}
            subgraph_ids = set()
            for record in results_nodes:
                n = record["n"]
                nodes[n.id] = {
                    "id": n.id,
                    "labels": list(n.labels),
                    "properties": dict(n)
                }
                subgraph_ids.add(n.id)

            edges = []
            if subgraph_ids:
                query_edges = """
                MATCH (n)-[r]->(m)
                WHERE id(n) IN $ids AND id(m) IN $ids
                RETURN r
                """
                results_edges = session.run(query_edges, ids=list(subgraph_ids))
                for record in results_edges:
                    r = record["r"]
                    edges.append({
                        "id": r.id,
                        "source": r.start_node.id,
                        "target": r.end_node.id,
                        "type": r.type,
                        "properties": dict(r)
                    })

        return {"nodes": list(nodes.values()), "links": edges}

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