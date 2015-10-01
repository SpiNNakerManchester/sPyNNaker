from spynnaker.pyNN.models.neuron.input_types.abstract_input_type \
    import AbstractInputType


class InputTypeCurrent(AbstractInputType):
    """ The current input type
    """

    def __init__(self):
        AbstractInputType.__init__(self)

    def get_global_weight_scale(self):
        return 1.0

    def get_n_input_type_parameters(self):
        return 0

    def get_input_type_parameters(self):
        return []

    def get_n_cpu_cycles_per_neuron(self, n_synapse_types):
        return 0
