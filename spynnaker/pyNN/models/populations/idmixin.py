# Copyright (c) 2017-2019 The University of Manchester
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

# Alternative implementation for
# https://github.com/NeuralEnsemble/PyNN/blob/master/pyNN/common/populations.py


class IDMixin(object):
    """
    Instead of storing IDs as integers, we store them as ID objects,
    which allows a syntax like::

        p[3,4].tau_m = 20.0

    where ``p`` is a Population object.
    """
    __slots__ = [
        "__id",
        "__population",
        "__vertex",
        "__recorder"
    ]
    __realslots__ = tuple("_IDMixin" + item for item in __slots__)

    def __init__(self, population, identifier):
        """
        :param ~spynnaker.pyNN.models.populations.Population population:
        :param int id:
        """
        self.__id = identifier
        self.__population = population

        # Get these two objects to make access easier
        # pylint: disable=protected-access
        self.__vertex = self.__population._vertex
        # pylint: disable=protected-access
        self.__recorder = self.__population._recorder

    @property
    def _vertex(self):
        return self.__vertex

    # NON-PYNN API CALLS
    @property
    def id(self):
        """
        :rtype: int
        """
        return self.__id

    def record(self, variables, to_file=None, sampling_interval=None):
        """ Record the given variable(s) of this cell.

        :param variables: either a single variable name or a list of variable
            names. For a given celltype class, celltype.recordable contains a
            list of variables that can be recorded for that celltype.
        :type variables: str or list(str)
        :param to_file:
            If specified, should be a Neo IO instance and write_data()
            will be automatically called when end() is called.
        :type to_file: neo.io.baseio.BaseIO or str
        :param int sampling_interval:
            should be a value in milliseconds, and an integer multiple of the
            simulation timestep.
        """
        self.__recorder.record(
            variables, to_file, sampling_interval, [self.__id])

    @property
    def initial_values(self):
        return self.__vertex.get_initial_state_values(
            self.__vertex.get_state_variables(), self.__id)

    def __getattr__(self, name):
        if name == "__vertex":
            raise KeyError("Shouldn't come through here!")
        return self.__vertex.get_parameter_values(name, self.__id)

    def __setattr__(self, name, value):
        if name in self.__realslots__:
            object.__setattr__(self, name, value)
            return
        return self.__vertex.set_parameter_values(name, value, self.__id)

    def set_parameters(self, **parameters):
        """ Set cell parameters, given as a sequence of parameter=value\
            arguments.
        """
        for (name, value) in parameters.items():
            self.__vertex.set_parameter_values(name, value, self.__id)

    def get_parameters(self):
        """ Return a dict of all cell parameters.

        :rtype: dict(str, ...)
        """
        return self.__vertex.get_parameter_values(
            self.__vertex.get_parameters(), self.__id)

    @property
    def celltype(self):
        """
        :rtype: AbstractPyNNModel
        """
        return self.__population.celltype

    @property
    def is_standard_cell(self):
        """
        :rtype: bool
        """
        raise NotImplementedError  # pragma: no cover

    @property
    def position(self):
        """ Return the cell position in 3D space.\
            Cell positions are stored in an array in the parent Population,\
            if any, or within the ID object otherwise. Positions are generated\
            the first time they are requested and then cached.

        :rtype: ~numpy.ndarray
        """
        return self.__population.positions[:, self.__id]   # pragma: no cover

    @position.setter
    def position(self, pos):
        """ Set the cell position in 3D space.\
            Cell positions are stored in an array in the parent Population.
        """
        self.__population.positions[self.__id] = pos   # pragma: no cover

    @property
    def local(self):
        """ Whether this cell is local to the current MPI node.

        :rtype: bool
        """
        # There are no MPI nodes!
        return True

    def inject(self, current_source):
        """ Inject current from a current source object into the cell.

        :param ~pyNN.neuron.standardmodels.electrodes.NeuronCurrentSource\
            current_source:
        """
        self.__vertex.inject(current_source, [self.__id])

    def get_initial_value(self, variable):
        """ Get the initial value of a state variable of the cell.

        :param str variable: The name of the variable
        :rtype: float
        """
        return self.__vertex.get_initial_state_values(variable, self.__id)

    def set_initial_value(self, variable, value):
        """ Set the initial value of a state variable of the cell.
        :param str variable: The name of the variable
        :param float value: The value of the variable
        """
        self.__vertex.set_initial_state_values(variable, value, self.__id)

    def initialize(self, **initial_values):
        """ Set the initial value of a state variable of the cell.

        """
        for variable, value in initial_values.items():
            self.__vertex.set_initial_state_values(variable, value, self.__id)

    def as_view(self):
        """ Return a PopulationView containing just this cell.

        :rtype: ~spynnaker.pyNN.models.populations.PopulationView
        """
        return self.__population[self.__id:self.__id+1]

    def __eq__(self, other):
        if not isinstance(other, IDMixin):
            return False
        return self.__vertex == other._vertex and self.__id == other.id

    def __ne__(self, other):
        if not isinstance(other, IDMixin):
            return True
        return not self.__eq__(other)

    def __str__(self):
        return str(self.__vertex) + "[" + str(self.__id) + "]"

    def __repr__(self):
        return repr(self.__vertex) + "[" + str(self.__id) + "]"
