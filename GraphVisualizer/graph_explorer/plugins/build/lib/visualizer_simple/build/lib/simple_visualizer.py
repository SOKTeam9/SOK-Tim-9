from jinja2 import Environment, FileSystemLoader
import json
from ..visualizer import Visualizer

class SimpleVisualizer(Visualizer):
    def __init__(self):
        pass

    def get_context(self, graph_data):
        """
        Vrati context koji će Django proslediti u template.
        """
        return {
            "nodes": json.dumps(graph_data["nodes"]),
            "edges": json.dumps(graph_data["links"]),
        }
    
    def visualize(self, graph_data):
        return self.get_context(graph_data)