from neo4j import GraphDatabase

import yaml

class YamlFileParser():
	def __init__(self, file_name, driver):
		self.file_name = file_name
		self.data = []
		self.driver = driver
		self.relationships = []
		
	def load(self):
		with open(self.file_name, "r") as f:
			self.data = yaml.safe_load(f)

			with self.driver.session() as session:
				session.execute_write(self.clear_database)
				session.execute_write(self.create_nodes)
				session.execute_write(self.create_relationships)

	def clear_database(self, tx):
		tx.run("MATCH (n) DETACH DELETE n")

	def create_nodes(self, tx):
		all_ids = set()

		group_list = self.data.values()
		for group in group_list:
			for item in group:
				all_ids.add(item["id"])
				
		for group_name, data_pool in self.data.items():
			keys_list = []
			for item in data_pool:
				keys_list = list(item.keys())
				break
			for single_data in data_pool: #single_data = recnik
				for key, value in single_data.items():
					if isinstance(value, list):
						for item in value:
							if item in all_ids:
								if key in keys_list:
									keys_list.remove(key)
								
								self.relationships.append((single_data["id"], item, key))
							else:
								break

				node_data = {k: v for k, v in single_data.items() if k in keys_list}
    			# Pripremi parametre za Cypher
				cypher_keys = ", ".join(f"{k}: ${k}" for k in node_data.keys())

    			# Pokreni CREATE
				tx.run(f"CREATE (:Node {{ {cypher_keys} }})", **node_data)

	def create_relationships(self, tx):
		for source_id, target_id, rel_type in self.relationships:
			rel_type_upper = rel_type.upper()
			query = f"""
            MATCH (a:Node {{id: $source_id}})
            MATCH (b:Node {{id: $target_id}})
            CREATE (a)-[:{rel_type_upper}]->(b)
        """
        
			tx.run(query, source_id=source_id, target_id=target_id)

#TEST
if __name__ == "__main__":
	uri = "neo4j://127.0.0.1:7687"
	username = "neo4j"
	password = "djomlaboss"

	# Kreiranje drajvera
	driver = GraphDatabase.driver(uri, auth=(username, password))

	parser = YamlFileParser("D:\\SOK\\SOK-Tim-9\\GraphVisualizer\\graph_explorer\\plugins\\data-source-plugin-yaml\\a.yaml", driver)
	parser.load()
	# Zatvaranje drajvera
	driver.close()