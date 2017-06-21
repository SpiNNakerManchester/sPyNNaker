from six import add_metaclass

from spinn_utilities.abstract_base import AbstractBase, abstractmethod

abstractstaticmethod = abstractmethod


@add_metaclass(AbstractBase)
class Recordable(object):
    """ Indicates that spikes can be recorded from this object
    """

    __slots__ = ()

    # Here we have to choose between using @abstractstatic or @staticmethod
    # Using both either fails or cause @abstractstatic to be ignored
    # However even abstractstatic only enforces that one of the
    # abstract_x_recordable interfaces implements the method not all.
    @staticmethod
    @abstractmethod
    def get_recordable_variable():
        """
        Gives the pynn name of the variable that this Interface deals with
        :return:
        """

    @property
    def recordable(self):
        """
        returns a list of the variables that can be recorded.

        Note This changing the resulting list will have no effect.
        :return: List[Str]
        """
        return self.get_all_possible_recordable_variables(self)

    @staticmethod
    def get_all_possible_recordable_variables(aclass):
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
        # This version only calls the direct subclasses of recordable.
        # So each abstract_x_recordable.get_recordable_variable()
        #   is only called once
        # But would fail if a abstract_x_recordable indirectly inherits
        #   Recordsble
        if not isinstance(aclass, type):
            aclass = type(aclass)
        variables = list()
        for sub in aclass.mro():
            if sub in Recordable.__subclasses__():
                variables.append(sub.get_recordable_variable())
        return variables

    @staticmethod
    def get_all_possible_recordable_variables1(aclass):
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
        # This version works even with indirect inheritence
        # But cause some get_recordable_variable() to be called more than once
        # So must use set
        if not isinstance(aclass, type):
            aclass = type(aclass)
        variables = set()
        for sub in aclass.mro():
            if issubclass(sub, Recordable) and not sub == Recordable:
                variables.add(sub.get_recordable_variable())
        return list(variables)

    @staticmethod
    def get_all_possible_recordable_variables2(module):
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
