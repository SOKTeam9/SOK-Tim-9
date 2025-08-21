from jinja2 import Environment, FileSystemLoader

class SimpleVisualizer:
    def __init__(self, template_dir="templates"):
        self.env = Environment(loader=FileSystemLoader(template_dir))

    def render(self, graph_data):
        template = self.env.get_template("simple-template.html")
        print(template)
        return template.render(
            nodes=graph_data["nodes"],
            edges=graph_data["edges"]
        )
