from six import add_metaclass
from abc import ABCMeta
from abc import abstractmethod


@add_metaclass(ABCMeta)
class AbstractHasFirstMachineTimeStep(object):
    """ Indicates an object for which the first machine timestep can be set
    """

    @abstractmethod
    def set_first_machine_time_step(self, first_machine_time_step):
        """ Sets the first machine time step that the simulation will be\
            started from
        """
