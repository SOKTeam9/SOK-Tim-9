from neo4j import GraphDatabase
from neo4j.time import Date, DateTime
from datetime import date, datetime
from neo4j.exceptions import ClientError
import re

# WORKSPACES = {
#     "ws1": "neo4j1",   # default baza
#     "ws2": "neo4j2",
#     "ws3": "neo4j3",
#     "ws4": "neo4j4",
#     "ws5": "neo4j5",
# }

def serialize_value(value):
    if isinstance(value, (Date, DateTime)):
        return str(value)  # npr. "2025-08-20"
    if isinstance(value, list):
        return [serialize_value(v) for v in value]
    if isinstance(value, dict):
        return {k: serialize_value(v) for k, v in value.items()}
    return value

def cypher_value(val):
    if isinstance(val, str) and val.lower() in ("true", "false"):
        return val.lower()
    if isinstance(val, (int, float)):
        return str(val)
    if isinstance(val, str):
        # ako je string u formatu YYYY-MM-DD, tretiraj kao datum
        if re.match(r"^\d{4}-\d{2}-\d{2}$", val):
            return f"date('{val}')"
        return f"'{val}'"
    raise ValueError(f"Unsupported type: {type(val)}")

class GraphHandler:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    # def get_graph_by_workspace(self, workspace_key):
    #     database = WORKSPACES.get(workspace_key, "neo4j1")  # fallback
    #     return self.get_graph(database=database)

    # def get_subgraph_by_workspace(self, workspace_key, filters):
    #     database = WORKSPACES.get(workspace_key, "neo4j1")
    #     return self.get_subgraph(filters, database=database)

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
                val_repr = cypher_value(val)

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
                        "properties": serialize_value(dict(n))
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
                            "properties": serialize_value(dict(r))
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
            
    def get_search_subgraph(self, filters=None, search_query=None, database="neo4j1"):
       
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
    
    def delete_and_get_empty_graph(self, database="neo4j1"):
        """
        Briše sve čvorove i relacije iz grafa, a zatim dobavlja prazan graf.

        Args:
            database (str): Naziv baze podataka.

        Returns:
            dict: Rečnik sa praznim listama za čvorove i veze.
        """
        # Cypher upit za brisanje svih čvorova i relacija
        delete_query = """
        MATCH (n)
        DETACH DELETE n
        """

        with self.driver.session(database=database) as session:
            try:
                # Izvrši upit za brisanje
                session.run(delete_query)
                print(f"Svi čvorovi i relacije su uspešno obrisani iz baze '{database}'.")
            except Exception as e:
                print(f"Greška prilikom brisanja grafa: {e}")
                # Vrati prazan graf čak i ako brisanje ne uspe
                return {"nodes": [], "links": []}

        # Nakon brisanja, pozovi get_graph() da bi vratio prazan graf
        # Ovo će potvrditi da je baza prazna
        return self.get_graph(database=database)

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