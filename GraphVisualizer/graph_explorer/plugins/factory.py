from .data_source_plugin_json.json_data_source_plugin import JSONGraphParser
from .data_source_plugin_xml.xml_data_source_plugin import XmlFileParser
from .data_source_plugin_yaml.yaml_data_source_plugin import YamlFileParser
from .visualizer_block.block_visualizer import BlockVisualizer
from .visualizer_simple.simple_visualizer import SimpleVisualizer
from neo4j import GraphDatabase

#FACTORY METHOD PATTERN
class ParserFactory:
    @staticmethod
    def create_parser(file_name, driver, file_type, database):
        file_type = file_type.lower()
        if file_type == "json":
            return JSONGraphParser(file_name, driver, None, database)
        elif file_type == "xml":
            return XmlFileParser(file_name, driver, database)
        elif file_type == "yaml":
            return YamlFileParser(file_name, driver, database)
        else:
            raise ValueError(f"Unsupported parser type: {file_type}")


class VisualizerFactory:
    @staticmethod
    def create_visualizer(vis_type, graph_data=None):
        vis_type = vis_type.lower()
        if vis_type == "block":
            return BlockVisualizer()
        elif vis_type == "simple":
            return SimpleVisualizer()
        else:
            raise ValueError(f"Unsupported visualizer type: {vis_type}")
        


    