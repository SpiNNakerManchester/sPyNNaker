from spinn_front_end_common.abstract_models.\
    abstract_changable_after_run import \
    AbstractChangableAfterRun
from spynnaker.pyNN.models.abstract_models.\
    abstract_population_initializable import \
    AbstractPopulationInitializable
from spynnaker.pyNN.models.abstract_models.\
    abstract_population_settable import \
    AbstractPopulationSettable
from spynnaker.pyNN.models.common.abstract_gsyn_recordable import \
    AbstractGSynRecordable
from spynnaker.pyNN.models.common.abstract_spike_recordable import \
    AbstractSpikeRecordable
from spynnaker.pyNN.models.common.abstract_v_recordable import \
    AbstractVRecordable
from spynnaker.pyNN.models.neuron.bag_of_neurons_vertex import \
    BagOfNeuronsVertex


class AbstractPopulationModel(
    AbstractPopulationInitializable, AbstractSpikeRecordable,
    AbstractVRecordable, AbstractGSynRecordable, AbstractPopulationSettable,
    AbstractChangableAfterRun):
    """
    AbstractPopulationModel: the model for neurons which take a synaptic matrix
    """

    model_variables = {'spikes_per_second', 'ring_buffer_sigma',
                       'incoming_spike_buffer_size', 'machine_time_step',
                       'time_scale_factor'}

    @staticmethod
    def create_vertex(bag_of_neurons, population_parameters):
        params = dict(population_parameters)
        params['bag_of_neurons'] = bag_of_neurons
        vertex = BagOfNeuronsVertex(**params)
        return vertex
