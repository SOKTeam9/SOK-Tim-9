from neo4j import GraphDatabase

import yaml

class Yaml_File_Parser():
	def __init__(self, file_name, driver):
		self.file_name = file_name
		self.data = []
		self.driver = driver
		self.relationships = []
		self.load()
		


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
		for group_name, data_pool in self.data.items():
			#data_pool = self.data[nodes] # lista recnika
			all_ids = {node['id'] for node in data_pool} #set svih id

			for single_data in data_pool: #single_data = recnik
				keys_list = list(single_data.keys())
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
			tx.run(
		        """
		        MATCH (a:Node {id: $source_id})
		        MATCH (b:Node {id: $target_id})
		        CREATE (a)-[:{rel_type.upper()}]->(b)
		        """,
				source_id=source_id,
				target_id=target_id
			)


if __name__ == "__main__":
	# Zameni ovim svojim kredencijalima iz Sandbox-a
	uri = "neo4j://127.0.0.1:7687"
	username = "neo4j"
	password = "djomlaboss"

	# Kreiranje drajvera
	driver = GraphDatabase.driver(uri, auth=(username, password))

	parser = Yaml_File_Parser("C:\\Users\\nexga\\OneDrive\\Desktop\\nesto\\test.yaml", driver)

	# Zatvaranje drajvera
	driver.close()