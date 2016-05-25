from pacman.model.partitionable_graph.partitionable_graph import \
    PartitionableGraph
from spynnaker.pyNN.models.population_based_objects import Assembly


class Grouper(object):
    """
    grouper: a function which takes a bag of neurons and maps them into vertices
    """

    def __call__(self, atom_mapping):

        # build a partitionable graph
        partitionable_graph = PartitionableGraph("grouped_application_graph")
        pop_to_vertex_mapping = dict()

        # for each model type build a monolithic vertex for them all
        for model_type in atom_mapping.keys():
            local_atom_mapping = dict(atom_mapping[model_type])
            while len(local_atom_mapping.keys()) != 0:
                self._handle_model_type(
                    local_atom_mapping, model_type, partitionable_graph,
                    pop_to_vertex_mapping)

        # handle projections
        self.handle_projections()

        return {'partitionable_graph': partitionable_graph,
                'pop_to_vertex_mapping': pop_to_vertex_mapping}

    def handle_projections(self):
        """

        :return:
        """
        pass

    def _handle_model_type(
            self, things_containing_model_type, model_type,
            partitionable_graph, pop_to_vertex_mapping):
        """

        :param things_containing_model_type:
        :param model_type:
        :param partitionable_graph:
        :param pop_to_vertex_mapping:
        :return:
        """

        atoms = list()

        # core based objects
        located = False
        has_constraints = False
        constraints = list()
        population_level_parameters = None

        # accumulate all atoms from those populations of this model type
        label = ""
        added_pops = list()
        for pop_pop_view_assembly in things_containing_model_type:

            # test if the population can be added to the current group.
            population_level_parameters, located, has_constraints, \
                constraints, added = self._check_population_for_addition(
                    pop_pop_view_assembly, atoms, label, located,
                    population_level_parameters,
                    things_containing_model_type, has_constraints,
                    constraints)

            # if added, add to pops to remove from this list.
            if added:
                added_pops.append(pop_pop_view_assembly)

        # remove added pops
        for pop in added_pops:
            del things_containing_model_type[pop]

        # build inputs for the vertex
        inputs = dict(population_level_parameters)
        inputs['label'] = label
        inputs['constraints'] = constraints
        inputs['model_class'] = model_type

        # create vertex and add to partitionable graph
        vertex = model_type.create_vertex(atoms, inputs)
        partitionable_graph.add_vertex(vertex)

    @staticmethod
    def _check_population_for_addition(
            pop_pop_view_assembly, atoms, label, located,
            population_level_parameters, things_containing_model_type,
            has_constraints, constraints):
        """

        :param pop_pop_view_assembly:
        :param atoms:
        :param label:
        :param located:
        :param population_level_parameters:
        :param things_containing_model_type:
        :param has_constraints:
        :param constraints:
        :return:
        """

        added = False
        # if first population, record data needed for comparison
        if not located:
            population_level_parameters = \
                pop_pop_view_assembly.population_parameters()
            if len(pop_pop_view_assembly.constraints) != 0:
                has_constraints = True
                constraints = pop_pop_view_assembly.constraints
            located = True
            atoms += things_containing_model_type[pop_pop_view_assembly]
            label += pop_pop_view_assembly.label
            added = True

        else: # not first population, therefore compare.
            correct_pop_level_parameters = True
            for param in population_level_parameters:
                first_param = population_level_parameters[param]
                second_param = \
                    pop_pop_view_assembly.population_parameters()[param]
                if first_param != second_param:
                    correct_pop_level_parameters = False

            # verify the pop is merge able
            if (correct_pop_level_parameters and not has_constraints and
                    len(pop_pop_view_assembly.constraints) == 0):
                atoms += things_containing_model_type[pop_pop_view_assembly]
                label += pop_pop_view_assembly.label
                added = True

        # return data items
        return population_level_parameters, located, has_constraints, \
            constraints, added
