from abc import ABC, abstractmethod

#STRATEGY PATTERN
class Visualizer(ABC):
    @abstractmethod
    def visualize(self, graph_data):
        """Svi vizualizeri moraju implementirati ovaj metod."""
        pass