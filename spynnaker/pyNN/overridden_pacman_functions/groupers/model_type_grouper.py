# pacman imports
from pacman.model.partitionable_graph.partitionable_graph import \
    PartitionableGraph

# spinnMachine imports
from spinn_machine.utilities.progress_bar import ProgressBar

# spynnaker imports
from spynnaker.pyNN.models.neuron.bag_of_neurons_vertex import \
    BagOfNeuronsVertex
from spynnaker.pyNN.overridden_pacman_functions.groupers.\
    abstract_grouper import AbstractGrouper

# general imports
import logging
from collections import OrderedDict

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

        # add progress bar
        progress_bar = ProgressBar(
            len(population_atom_mapping.keys()),
            "grouping atoms together to create vertices")

        # for each model type build a monolithic vertex for them all
        for model_type in population_atom_mapping.keys():
            local_atom_mapping = dict(population_atom_mapping[model_type])
            while len(local_atom_mapping.keys()) != 0:
                self._handle_model_type(
                    local_atom_mapping, model_type, partitionable_graph,
                    pop_to_vertex_mapping, vertex_to_pop_mapping)
            progress_bar.update()
        progress_bar.end()

        # handle projections
        self.handle_projections(
            projections, population_atom_mapping, pop_to_vertex_mapping,
            user_max_delay, partitionable_graph, using_virtual_board)

        return {'partitionable_graph': partitionable_graph,
                'pop_to_vertex_mapping': pop_to_vertex_mapping,
                'vertex_to_pop_mapping': vertex_to_pop_mapping}

    def _handle_model_type(
            self, things_containing_model_type, model_type,
            partitionable_graph, pop_to_vertex_mapping, vertex_to_pop_mapping):
        """
        takes the model type and tries to build as little vertices to cover
        the different parameters available.
        :param things_containing_model_type: local atom mapping for a model type
        :param model_type: the model type in question
        :param partitionable_graph: the partitionable graph to add vertices into
        :param pop_to_vertex_mapping: the overall vertex to population map
        :return: None
        """

        atoms = list()

        # core based objects
        located = False
        has_constraints = False
        constraints = list()
        fixed_parameters = None
        internal_pop_to_atom_mapping = dict()

        # accumulate all atoms from those populations of this model type
        label = ""
        added_pops = list()
        for pop_pop_view_assembly in things_containing_model_type:

            # test if the population can be added to the current group.
            located, has_constraints, constraints, added, fixed_parameters = \
                self._check_population_for_addition(
                    pop_pop_view_assembly, located,
                    things_containing_model_type,
                    has_constraints, constraints, fixed_parameters)

            # if added, add to pops to remove from this list.
            if added:
                # update mapping object
                internal_pop_to_atom_mapping[pop_pop_view_assembly] = \
                    (len(atoms),
                     len(atoms) + len(
                         things_containing_model_type[pop_pop_view_assembly]))

                # add to atoms and label objects for the vertex
                atoms += things_containing_model_type[pop_pop_view_assembly]
                label += pop_pop_view_assembly.label

                # holder for array iteration modifications
                added_pops.append(pop_pop_view_assembly)

        # remove added pops
        for pop in added_pops:
            del things_containing_model_type[pop]

        # build inputs for the vertex
        inputs = dict()
        inputs['label'] = label
        inputs['constraints'] = constraints

        if issubclass(model_type, BagOfNeuronsVertex):
            inputs['model_class'] = model_type

        # create vertex and add to partitionable graph
        vertex = model_type.create_vertex(atoms, inputs)
        partitionable_graph.add_vertex(vertex)

        # update pop to vertex mapping
        for pop in added_pops:
            pop_to_vertex_mapping[pop] = (
                vertex,
                internal_pop_to_atom_mapping[pop][0],
                internal_pop_to_atom_mapping[pop][1])

            pop._mapped_vertices = pop_to_vertex_mapping[pop]

        # update vertex to pop mapping
        vertex_to_pop_mapping[vertex] = list()
        for pop in added_pops:
            vertex_to_pop_mapping[vertex].append(
                (pop, internal_pop_to_atom_mapping[pop][0],
                 internal_pop_to_atom_mapping[pop][1]))

    @staticmethod
    def _check_population_for_addition(
            pop_pop_view_assembly, located, things_containing_model_type,
            has_constraints, constraints, fixed_parameters):
        """

        :param pop_pop_view_assembly:
        :param located:
        :param has_constraints:
        :param constraints:
        :param fixed_parameters:
        :return:
        """

        added = False
        # if first population, record data needed for comparison
        if not located:
            if len(pop_pop_view_assembly.constraints) != 0:
                has_constraints = True
                constraints = pop_pop_view_assembly.constraints

            fixed_parameters = \
                things_containing_model_type[pop_pop_view_assembly][0].\
                population_parameters

            located = True
            added = True

        else:  # not first population, therefore compare
            # verify the pop is merge able
            if (not has_constraints and
                    len(pop_pop_view_assembly.constraints) == 0):

                # other fixed parameter extraction
                other_fixed_parameters = \
                    things_containing_model_type[pop_pop_view_assembly][0].\
                    population_parameters

                added = True
                for parameter_name in fixed_parameters:
                    if (other_fixed_parameters[parameter_name] !=
                            fixed_parameters[parameter_name]):
                        added = False

        # return data items
        return located, has_constraints, \
            constraints, added, fixed_parameters
