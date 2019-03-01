from pacman.model.decorators.overrides import overrides
from spynnaker.pyNN.models.neuron import AbstractPopulationVertex
from spynnaker.pyNN.models.neuron import SynapticManager
from spynnaker.pyNN.models.abstract_pynn_model import AbstractPyNNModel

from pacman.model.constraints.partitioner_constraints\
    import SameAtomsAsVertexConstraint


DEFAULT_MAX_ATOMS_PER_CORE = 255

_population_parameters = {
    "spikes_per_second": None, "ring_buffer_sigma": None,
    "incoming_spike_buffer_size": None
}


class AbstractPyNNNeuronModel(AbstractPyNNModel):

    __slots__ = ("_model")

    default_population_parameters = _population_parameters

    def __init__(self, model):
        self._model = model

    @classmethod
    def set_model_max_atoms_per_core(cls, n_atoms=DEFAULT_MAX_ATOMS_PER_CORE):
        super(AbstractPyNNNeuronModel, cls).set_model_max_atoms_per_core(
            n_atoms)

    @classmethod
    def get_max_atoms_per_core(cls):
        if cls not in super(AbstractPyNNNeuronModel, cls)._max_atoms_per_core:
            return DEFAULT_MAX_ATOMS_PER_CORE
        return super(AbstractPyNNNeuronModel, cls).get_max_atoms_per_core()


    @overrides(AbstractPyNNModel.create_vertex,
               additional_arguments=_population_parameters.keys())
    def create_vertex(
            self, n_neurons, label, constraints, spikes_per_second,
            ring_buffer_sigma, incoming_spike_buffer_size):

        max_atoms = self.get_max_atoms_per_core()

        vertices = list()

        vertices.append(AbstractPopulationVertex(
            n_neurons, label+"_neuron_vertex", constraints, max_atoms, spikes_per_second,
            ring_buffer_sigma, self._model, self))

        if constraints == None:
            syn_constraints = list()
        else:
            syn_constraints = constraints

        syn_constraints.append(SameAtomsAsVertexConstraint(vertices[0]))

        for index in range(vertices[0].get_n_synapse_types()):
            vertices.append(SynapticManager(1, index, n_neurons, syn_constraints,
                                            label+"_syn_vertex_"+str(index), max_atoms,
                                            self._model.get_global_weight_scale(),
                                            ring_buffer_sigma, spikes_per_second,
                                            incoming_spike_buffer_size))

        for i in range(len(vertices)):
            vertices[i].connected_app_vertices = (vertices[:i] + vertices[i+1:])

        return vertices
