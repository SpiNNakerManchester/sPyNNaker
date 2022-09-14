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

from spynnaker.pyNN.data import SpynnakerDataView


class IDMixin(object):
    """
    Instead of storing IDs as integers, we store them as ID objects,
    which allows a syntax like::

        p[3,4].tau_m = 20.0

    where ``p`` is a Population object.
    """
    __slots__ = ("__id", "__population")
    __realslots__ = tuple("_IDMixin" + item for item in __slots__)

    def __init__(self, population, id):  # pylint: disable=redefined-builtin
        """
        :param ~spynnaker.pyNN.models.populations.Population population:
        :param int id:
        """
        self.__id = id
        self.__population = population

    # NON-PYNN API CALLS
    @property
    def id(self):
        """
        :rtype: int
        """
        return self.__id

    @property
    def _population(self):
        return self.__population

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
        self.__population.record(variables, to_file, sampling_interval,
                                 [self.__id])

    def __getattr__(self, name):
        if name == "initial_values":
            return self.__population._get_initial_values(self.__id)
        try:
            return self.__population._get_by_selector(
                selector=self.__id, parameter_names=name)[0]
        except Exception as e:
            try:
                # try initialisable variable
                return self.__population._get_initial_value(
                    selector=self.__id, variable=name)[0]
            except Exception:  # pylint: disable=broad-except
                # that failed too so raise the better original exception
                pass
            raise e

    def __setattr__(self, name, value):
        if name in self.__realslots__:
            object.__setattr__(self, name, value)
            return
        try:
            self.__population.set_by_selector(self.__id, name, value)
        except Exception as e:
            try:
                # try initialisable variable
                return self.__population._initialize(
                    selector=self.__id, variable=name, value=value)
            except Exception:  # pylint: disable=broad-except
                # that failed too so raise the better original exception
                pass
            raise e

    def set_parameters(self, **parameters):
        """ Set cell parameters, given as a sequence of parameter=value\
            arguments.
        """
        for (name, value) in parameters.items():
            self.__population.set_by_selector(self.__id, name, value)

    def get_parameters(self):
        """ Return a dict of all cell parameters.

        :rtype: dict(str, ...)
        """
        results = dict()
        for name in self.celltype.get_parameter_names():
            # pylint: disable=protected-access
            results[name] = self.__population._get_by_selector(self.__id, name)
        return results

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

    def _set_position(self, pos):
        """ Set the cell position in 3D space.\
            Cell positions are stored in an array in the parent Population.
        """
        self.__population.positions[self.__id] = pos   # pragma: no cover

    def _get_position(self):
        """ Return the cell position in 3D space.\
            Cell positions are stored in an array in the parent Population,\
            if any, or within the ID object otherwise. Positions are generated\
            the first time they are requested and then cached.

        :rtype: ~numpy.ndarray
        """
        return self.__population.positions[:, self.__id]   # pragma: no cover

    position = property(_get_position, _set_position)

    @property
    def local(self):
        """ Whether this cell is local to the current MPI node.

        :rtype: bool
        """
        return self.__population.is_local(self.__id)

    def inject(self, current_source):
        """ Inject current from a current source object into the cell.

        :param ~pyNN.neuron.standardmodels.electrodes.NeuronCurrentSource\
            current_source:
        """
        # pylint: disable=protected-access
        self.__population._vertex.inject(current_source, [self.__id])
        current_source.set_population(self.__population)
        SpynnakerDataView.set_requires_mapping()

    def get_initial_value(self, variable):
        """ Get the initial value of a state variable of the cell.

        :param str variable: The name of the variable
        :rtype: float
        """
        # pylint: disable=protected-access
        return self.__population._get_initial_value(variable, self.__id)

    def set_initial_value(self, variable, value):
        """ Set the initial value of a state variable of the cell.
        :param str variable: The name of the variable
        :param float value: The value of the variable
        """
        # pylint: disable=protected-access
        self.__population._initialize(variable, value, self.__id)

    def initialize(self, **initial_values):
        """ Set the initial value of a state variable of the cell.

        """
        for variable, value in initial_values.items():
            # pylint: disable=protected-access
            self.__population._initialize(variable, value, self.__id)

    def as_view(self):
        """ Return a PopulationView containing just this cell.

        :rtype: ~spynnaker.pyNN.models.populations.PopulationView
        """
        return self.__population[self.__id]

    def __eq__(self, other):
        if not isinstance(other, IDMixin):
            return False
        return self.__population == other._population and \
            self.__id == other.id

    def __ne__(self, other):
        if not isinstance(other, IDMixin):
            return True
        return not self.__eq__(other)

    def __str__(self):
        return str(self.__population) + "[" + str(self.__id) + "]"

    def __repr__(self):
        return repr(self.__population) + "[" + str(self.__id) + "]"
