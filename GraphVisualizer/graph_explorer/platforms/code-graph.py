from neo4j import GraphDatabase
from datetime import date, timedelta

# Konekcija na Neo4j
URI = "neo4j://127.0.0.1:7687"
USER = "neo4j"
PASSWORD = "djomlaboss"

driver = GraphDatabase.driver(URI, auth=(USER, PASSWORD))


def clear_database(tx):
    tx.run("MATCH (n) DETACH DELETE n")


def create_nodes(tx):
    base_date = date(2023, 1, 1)

    nodes = [
        {"id": 0, "name": "Alpha", "type": "Category", "value": 42, "createdAt": base_date},
        {"id": 1, "name": "Beta", "type": "Category", "value": 36, "createdAt": base_date + timedelta(days=1)},
        {"id": 2, "name": "Gamma", "type": "Category", "value": 27, "createdAt": base_date + timedelta(days=2)},
        {"id": 3, "name": "Delta", "type": "Subcategory", "value": 10, "createdAt": base_date + timedelta(days=3)},
        {"id": 4, "name": "Epsilon", "type": "Subcategory", "value": 12, "createdAt": base_date + timedelta(days=4)},
        {"id": 5, "name": "Zeta", "type": "Subcategory", "value": 18, "createdAt": base_date + timedelta(days=5)},
        {"id": 6, "name": "Eta", "type": "Subcategory", "value": 7, "createdAt": base_date + timedelta(days=6)},
        {"id": 7, "name": "Theta", "type": "Item", "value": 15, "createdAt": base_date + timedelta(days=7)},
        {"id": 8, "name": "Iota", "type": "Item", "value": 20, "createdAt": base_date + timedelta(days=8)},
        {"id": 9, "name": "Kappa", "type": "Item", "value": 5, "createdAt": base_date + timedelta(days=9)},
        {"id": 10, "name": "Lambda", "type": "Item", "value": 33, "createdAt": base_date + timedelta(days=10)},
        {"id": 11, "name": "Mu", "type": "Item", "value": 29, "createdAt": base_date + timedelta(days=11)},
        {"id": 12, "name": "Nu", "type": "Item", "value": 22, "createdAt": base_date + timedelta(days=12)},
        {"id": 13, "name": "Xi", "type": "Tag", "value": 17, "createdAt": base_date + timedelta(days=13)},
        {"id": 14, "name": "Omicron", "type": "Tag", "value": 25, "createdAt": base_date + timedelta(days=14)},
        {"id": 15, "name": "Pi", "type": "Tag", "value": 3, "createdAt": base_date + timedelta(days=15)},
        {"id": 16, "name": "Rho", "type": "Tag", "value": 8, "createdAt": base_date + timedelta(days=16)},
        {"id": 17, "name": "Sigma", "type": "Tag", "value": 9, "createdAt": base_date + timedelta(days=17)},
        {"id": 18, "name": "Tau", "type": "Tag", "value": 14, "createdAt": base_date + timedelta(days=18)},
        {"id": 19, "name": "Upsilon", "type": "Tag", "value": 11, "createdAt": base_date + timedelta(days=19)},
    ]

    for n in nodes:
        tx.run(
            """
            CREATE (:Node {id: $id, name: $name, type: $type, value: $value, createdAt: date($createdAt)})
            """,
            id=n["id"],
            name=n["name"],
            type=n["type"],
            value=n["value"],
            createdAt=n["createdAt"].isoformat()
        )


def create_relationships(tx):
    # Hijerarhija + ciklusi (sve isti tip veze: CONNECTED_TO)
    relationships = [
        # Categories -> Subcategories
        (0, 3), (0, 4),
        (1, 5), (1, 6),
        (2, 4), (2, 6),

        # Subcategories -> Items
        (3, 7), (3, 8),
        (4, 9), (4, 10),
        (5, 11),
        (6, 12),

        # Items -> Tags
        (7, 13), (8, 14),
        (9, 15), (10, 16),
        (11, 17), (12, 18),

        # Tags -> vraćaju unazad (ciklusi)
        (13, 0),   # Xi → Alpha
        (14, 1),   # Omicron → Beta
        (15, 3),   # Pi → Delta
        (16, 7),   # Rho → Theta
        (17, 2),   # Sigma → Gamma
        (18, 5),   # Tau → Zeta
        (19, 0),   # Upsilon → Alpha
    ]

    for start, end in relationships:
        tx.run("""
            MATCH (a:Node {id: $start}), (b:Node {id: $end})
            CREATE (a)-[:CONNECTED_TO]->(b)
        """, start=start, end=end)


def main():
    with driver.session() as session:
        session.execute_write(clear_database)
        session.execute_write(create_nodes)
        session.execute_write(create_relationships)

    print("✅ Hijerarhijski graf sa 20 čvorova, datumima i ciklusima kreiran.")


if __name__ == "__main__":
    main()
