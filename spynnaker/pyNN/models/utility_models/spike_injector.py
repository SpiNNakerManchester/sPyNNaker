from pacman.model.decorators import overrides
from spinn_front_end_common.abstract_models \
    import AbstractProvidesOutgoingPartitionConstraints
from spinn_front_end_common.utility_models import ReverseIpTagMultiCastSource

from pacman.model.constraints.key_allocator_constraints \
    import ContiguousKeyRangeContraint


class SpikeInjector(ReverseIpTagMultiCastSource,
                    AbstractProvidesOutgoingPartitionConstraints):
    """ An Injector of Spikes for PyNN populations.  This only allows the user\
        to specify the virtual_key of the population to identify the population
    """

    default_parameters = {
        'label': "spikeInjector", 'port': None, 'virtual_key': None}

    def __init__(
            self, n_neurons, label=default_parameters['label'],
            port=default_parameters['port'],
            virtual_key=default_parameters['virtual_key']):

        ReverseIpTagMultiCastSource.__init__(
            self, n_keys=n_neurons, label=label, receive_port=port,
            virtual_key=virtual_key, reserve_reverse_ip_tag=True)

        AbstractProvidesOutgoingPartitionConstraints.__init__(self)

    @overrides(AbstractProvidesOutgoingPartitionConstraints.
               get_outgoing_partition_constraints)
    def get_outgoing_partition_constraints(self, partition):
        constraints = ReverseIpTagMultiCastSource\
            .get_outgoing_partition_constraints(self, partition)
        constraints.append(ContiguousKeyRangeContraint())
        return constraints
