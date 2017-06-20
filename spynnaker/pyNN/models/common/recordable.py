class Recordable(object):
    """ Indicates that spikes can be recorded from this object
    """

    __slots__ = ()

    @property
    def recordable(self):
        """
        returns a list of the variables that can be recorded.

        Note This changing the resulting list will have no effect.
        :return: List[Str]
        """
        return self.get_all_possible_recordable_variables(self)

    @staticmethod
    def get_all_possible_recordable_variables(module):
        """
        returns a list of the variables that can be recorded.

        Typically called with an implmenation of one or more of the
            Abstract _x_Recobable interfaces. If not it turns an empty list.

        Note This changing the resulting list will have no effect.
        :param module: Object to check if it implements any of the
            Abstract _x_Recobable interfaces.
        :type module: Recordable
        :return: List[Str]
        """
        from spynnaker.pyNN.models.common.abstract_gsyn_excitatory_recordable \
            import AbstractGSynExcitatoryRecordable
        from spynnaker.pyNN.models.common.abstract_gsyn_inhibitory_recordable \
            import AbstractGSynInhibitoryRecordable
        from spynnaker.pyNN.models.common.abstract_spike_recordable \
            import AbstractSpikeRecordable
        from spynnaker.pyNN.models.common.abstract_v_recordable \
            import AbstractVRecordable
        variables = list()
        if isinstance(module, AbstractSpikeRecordable):
            variables.append('spikes')
        if isinstance(module, AbstractVRecordable):
            variables.append('v')
        if isinstance(module, AbstractGSynExcitatoryRecordable):
            variables.append('gsyn_exc')
        if isinstance(module, AbstractGSynInhibitoryRecordable):
            variables.append('gsyn_inh')
        return variables
