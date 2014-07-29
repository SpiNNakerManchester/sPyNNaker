from spynnaker.pyNN.models.abstract_models.abstract_recordable_vertex import \
    AbstractRecordableVertex
from spynnaker.pyNN.models.abstract_models.abstract_data_specable_vertex import \
    AbstractDataSpecableVertex
from spynnaker.pyNN.models.abstract_models.\
    abstract_partitionable_population_vertex import AbstractPartitionableVertex

from enum import Enum
from spynnaker.pyNN.models.abstract_models.abstract_routerable_vertex import \
    AbstractRouterableVertex


class AbstractSpikeSource(AbstractRecordableVertex, AbstractPartitionableVertex,
                          AbstractDataSpecableVertex, AbstractRouterableVertex):

    _SPIKE_SOURCE_REGIONS = Enum(
        value="_SPIKE_SOURCE_REGIONS",
        names=[('SYSTEM_REGION', 0),
               ('BLOCK_INDEX_REGION', 1),
               ('SPIKE_DATA_REGION', 2),
               ('SPIKE_HISTORY_REGION', 3)])

    def __init__(self, label, n_neurons, constraints, max_atoms_per_core):
        AbstractPartitionableVertex.__init__(
            self, n_atoms=n_neurons, label=label, constraints=constraints,
            max_atoms_per_core=max_atoms_per_core)
        AbstractRecordableVertex.__init__(self, label)
        AbstractDataSpecableVertex.__init__(self, label=label,
                                            n_atoms=n_neurons)
        AbstractRouterableVertex.__init__(self)

    def _write_setup_info(self, spec, spike_history_region_sz):
        """
        Write information used to control the simulationand gathering of
        results. Currently, this means the flag word used to signal whether
        information on neuron firing and neuron potential is either stored
        locally in a buffer or passed out of the simulation for storage/display
         as the simulation proceeds.

        The format of the information is as follows:
        Word 0: Flags selecting data to be gathered during simulation.
            Bit 0: Record spike history
        """

        # What recording commands wereset for the parent
        # pynn_population.py?
        recording_info = 0
        if (spike_history_region_sz > 0) and self._record:
            recording_info |= self._SPIKE_SOURCE_REGIONS.RECORD_SPIKE_BIT
        recording_info |= 0xBEEF0000
        # Write this to the system region (to be picked up by the simulation):
        spec.switchWriteFocus(region=self._SPIKE_SOURCE_REGIONS.SYSTEM_REGION)
        spec.write(data=recording_info)
        spec.write(data=spike_history_region_sz)
        spec.write(data=0)
        spec.write(data=0)