from spynnaker.pyNN.models.neuron.inputs_components.\
    abstract_input_type_component import AbstractInputTypeComponent


class CurrentInputType(AbstractInputTypeComponent):
    """ Represents parameters needed for dealing with current input (none)
    """

    def __init__(self):
        pass

    def get_n_input_parameters(self):
        return 0

    def get_input_component_source_name(self):
        # TODO: replace with header name when available
        return ""

    def get_input_weight_scale(self):
        return 1.0
