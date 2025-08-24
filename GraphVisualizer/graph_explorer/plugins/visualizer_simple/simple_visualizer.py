from jinja2 import Environment, FileSystemLoader

class SimpleVisualizer:
    def __init__(self):
        pass

    def get_context(self, graph_data):
        """
        Vrati context koji će Django proslediti u template.
        """
        return {
            "nodes": graph_data["nodes"],
            "edges": graph_data["links"],
        }