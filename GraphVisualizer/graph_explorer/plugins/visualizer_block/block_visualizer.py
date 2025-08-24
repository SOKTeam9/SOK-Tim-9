import json

class BlockVisualizer:
    def __init__(self, graph_data):
        """
        graph_data = dict sa ključevima 'nodes' i 'links'
        {
          "nodes": [{"id": 1, "label": "User", "properties": {...}}, ...],
          "links": [{"source": 0, "target": 1, "type": "RELATION"}, ...]
        }
        """
        self.graph_data = graph_data

    def render(self):
        # Pretvori graph_data u JSON string
        graph_json = json.dumps(self.graph_data)

        # HTML + JS za D3 vizualizaciju
        html = f"""
        <div id="graph"></div>
        <script src="https://d3js.org/d3.v3.min.js"></script>
        <script>
        var graph = {graph_json};

        var width = 800, height = 600;

        var force = d3.layout.force()
            .charge(-300)
            .linkDistance(150)
            .size([width, height]);

        var svg = d3.select("#graph").append("svg")
            .attr("width", width)
            .attr("height", height);

        var idToIndex = {{}};
        graph.nodes.forEach(function(d, i) {{
            idToIndex[d.id] = i;
        }});

        graph.links.forEach(function(d) {{
            d.source = idToIndex[d.source];
            d.target = idToIndex[d.target];
        }});

        force
          .nodes(graph.nodes)
          .links(graph.links)
          .start();

        var link = svg.selectAll(".link")
            .data(graph.links)
            .enter().append("line")
            .attr("class", "link")
            .style("stroke", "#999")
            .style("stroke-opacity", "0.6")
            .style("stroke-width", "2px");

        var node = svg.selectAll(".node")
            .data(graph.nodes)
            .enter().append("g")
            .attr("class", "node")
            .call(force.drag);

        node.append("circle")
            .attr("r", 20)
            .style("fill", "#69b3a2");

        node.append("text")
            .attr("dy", -25)
            .attr("text-anchor", "middle")
            .text(function(d) {{ return d.label; }});

        // tooltip/blok prikaz podataka
        node.append("title")
            .text(function(d) {{
                return JSON.stringify(d.properties, null, 2);
            }});

        force.on("tick", function() {{
            link.attr("x1", function(d) {{ return d.source.x; }})
                .attr("y1", function(d) {{ return d.source.y; }})
                .attr("x2", function(d) {{ return d.target.x; }})
                .attr("y2", function(d) {{ return d.target.y; }});

            node.attr("transform", function(d) {{
                return "translate(" + d.x + "," + d.y + ")";
            }});
        }});
        </script>
        """
        return html
