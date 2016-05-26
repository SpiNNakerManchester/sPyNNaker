from pacman.model.partitionable_graph.partitionable_graph import \
    PartitionableGraph


class Grouper(object):
    """
    grouper: a function which takes a bag of neurons and maps them into vertices
    """

    def __call__(
            self, population_atom_mapping, pop_view_atom_mapping,
            assembly_atom_mapping, projections):

        # build a partitionable graph
        partitionable_graph = PartitionableGraph("grouped_application_graph")
        pop_to_vertex_mapping = dict()

        # for each model type build a monolithic vertex for them all
        for model_type in population_atom_mapping.keys():
            local_atom_mapping = dict(population_atom_mapping[model_type])
            while len(local_atom_mapping.keys()) != 0:
                self._handle_model_type(
                    local_atom_mapping, model_type, partitionable_graph,
                    pop_to_vertex_mapping)

        # handle projections
        self.handle_projections(
            projections, population_atom_mapping, pop_to_vertex_mapping)

        return {'partitionable_graph': partitionable_graph,
                'pop_to_vertex_mapping': pop_to_vertex_mapping}

    def handle_projections(
            self, projections, population_atom_mapping, pop_to_vertex_mapping):
        """

        :return:
        """


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
        internal_pop_to_atom_mapping = dict()

        # accumulate all atoms from those populations of this model type
        label = ""
        added_pops = list()
        for pop_pop_view_assembly in things_containing_model_type:

            # test if the population can be added to the current group.
            population_level_parameters, located, has_constraints, \
                constraints, added = self._check_population_for_addition(
                    pop_pop_view_assembly, located,
                    population_level_parameters, has_constraints,
                    constraints)

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
        inputs = dict(population_level_parameters)
        inputs['label'] = label
        inputs['constraints'] = constraints
        inputs['model_class'] = model_type

        # create vertex and add to partitionable graph
        vertex = model_type.create_vertex(atoms, inputs)
        partitionable_graph.add_vertex(vertex)

        # update pop to vertex mapping
        for pop in added_pops:
            pop_to_vertex_mapping[pop] = dict()
            pop_to_vertex_mapping[pop][vertex] = (
                internal_pop_to_atom_mapping[pop_pop_view_assembly][0],
                internal_pop_to_atom_mapping[pop_pop_view_assembly][1])

    @staticmethod
    def _check_population_for_addition(
            pop_pop_view_assembly, located, population_level_parameters,
            has_constraints, constraints):
        """

        :param pop_pop_view_assembly:
        :param located:
        :param population_level_parameters:
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
                added = True

        # return data items
        return population_level_parameters, located, has_constraints, \
            constraints, added
