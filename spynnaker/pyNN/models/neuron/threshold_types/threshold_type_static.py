from spynnaker.pyNN.models.neural_properties.neural_parameter \
    import NeuronParameter
from data_specification.enums.data_type import DataType
from spynnaker.pyNN.models.neuron.threshold_types.abstract_threshold_type \
    import AbstractThresholdType


class ThresholdTypeStatic(AbstractThresholdType):
    """ A threshold that is a static value
    """

    def __init__(self, v_thresh):
        AbstractThresholdType.__init__(self)
        self._v_thresh = v_thresh

    def get_n_threshold_parameters(self):
        return 1

    def get_threshold_parameters(self):
        return [
            NeuronParameter(self._v_thresh, DataType.S1615)
        ]
