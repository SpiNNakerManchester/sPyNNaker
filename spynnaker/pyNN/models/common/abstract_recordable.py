from six import add_metaclass
from spinn_utilities.abstract_base import AbstractBase, abstractproperty


@add_metaclass(AbstractBase)
class AbstractRecordable(object):
    """ Indicates that spikes can be recorded from this object
    """

    __slots__ = ()

    @abstractproperty
    def recordable(self):
        """
        returns a list of the variables that can be recorded.

        Note This changing the resulting list will have no effect.
        :return: List[Str]
        """

"""
    possible implementation
from spynnaker.pyNN.models.common.abstract_gsyn_excitatory_recordable import \
    AbstractGSynExcitatoryRecordable
from spynnaker.pyNN.models.common.abstract_gsyn_inhibitory_recordable import \
    AbstractGSynInhibitoryRecordable
from spynnaker.pyNN.models.common.abstract_spike_recordable import \
    AbstractSpikeRecordable
from spynnaker.pyNN.models.common.abstract_v_recordable import \
    AbstractVRecordable

    def recordable(self):
        variables = list()
        if isinstance(self. AbstractSpikeRecordable):
            variables.append('spikes')
        if isinstance(self, AbstractVRecordable):
            variables.append('v')
        if isinstance(self, AbstractGSynExcitatoryRecordable):
            variables.append('gsyn_exc')
        if isinstance(self, AbstractGSynInhibitoryRecordable):
            variables.append('gsyn_inh')
        return variables
"""