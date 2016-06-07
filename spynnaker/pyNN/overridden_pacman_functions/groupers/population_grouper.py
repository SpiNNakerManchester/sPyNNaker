from collections import OrderedDict
from pacman.model.partitionable_graph.partitionable_graph import \
    PartitionableGraph

from spinn_machine.utilities.progress_bar import ProgressBar
from spynnaker.pyNN.models.neuron.abstract_population_model import \
    AbstractPopulationModel
from spynnaker.pyNN.overridden_pacman_functions.groupers.\
    abstract_grouper import AbstractGrouper


import logging
logger = logging.getLogger(__name__)


class Grouper(AbstractGrouper):
    """
    grouper: a function which takes a bag of neurons and maps them into vertices
    """
    
    def __init__(self):
        AbstractGrouper.__init__(self)

    def __call__(
            self, population_atom_mapping, projections, user_max_delay,
            using_virtual_board):

        # build a partitionable graph
        partitionable_graph = PartitionableGraph("grouped_application_graph")
        pop_to_vertex_mapping = dict()
        vertex_to_pop_mapping = OrderedDict()

        progress_bar = ProgressBar(
            len(population_atom_mapping.keys()),
            "grouping atoms together to create vertices")

        # for each model type build a monolithic vertex for them all
        for model_type in population_atom_mapping.keys():
            for pop in population_atom_mapping[model_type]:
                atoms = population_atom_mapping[model_type][pop]

                # build inputs for the vertex
                inputs = dict()
                inputs['label'] = pop.label
                inputs['constraints'] = pop.constraints

                if issubclass(model_type, AbstractPopulationModel):
                    inputs['model_class'] = model_type

                # create vertex and add to partitionable graph
                vertex = model_type.create_vertex(atoms, inputs)
                partitionable_graph.add_vertex(vertex)

                # update pop to vertex mapping
                pop_to_vertex_mapping[pop] = (vertex, 0, len(atoms))
                pop._mapped_vertices = pop_to_vertex_mapping[pop]

                # update vertex to pop mapping
                vertex_to_pop_mapping[vertex] = list()
                vertex_to_pop_mapping[vertex].append((pop, 0, len(atoms)))

            progress_bar.update()
        progress_bar.end()

        # handle projections
        self.handle_projections(
            projections, population_atom_mapping, pop_to_vertex_mapping,
            user_max_delay, partitionable_graph, using_virtual_board)

        return {'partitionable_graph': partitionable_graph,
                'pop_to_vertex_mapping': pop_to_vertex_mapping,
                'vertex_to_pop_mapping': vertex_to_pop_mapping}