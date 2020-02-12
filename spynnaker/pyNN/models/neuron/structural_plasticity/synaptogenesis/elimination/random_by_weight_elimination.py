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

from spinn_utilities.overrides import overrides
from .abstract_elimination import AbstractElimination


class RandomByWeightElimination(AbstractElimination):
    """ Elimination Rule that depends on the weight of a synapse
    """

    __slots__ = [
        "__prob_elim_depressed",
        "__prob_elim_potentiated",
        "__threshold"
    ]

    def __init__(
            self, threshold, prob_elim_depressed=0.0245,
            prob_elim_potentiated=1.36 * 10 ** -4):
        """
        :param float threshold:
            Below this weight is considered depression, above or equal to this
            weight is considered potentiation (or the static weight of the
            connection on static weight connections)
        :param float prob_elim_depressed:
            The probability of elimination if the weight has been depressed
            (ignored on static weight connections)
        :param float prob_elim_potentiated:
            The probability of elimination of the weight has been potentiated
            or has not changed (and also used on static weight connections)
        """
        self.__prob_elim_depressed = prob_elim_depressed
        self.__prob_elim_potentiated = prob_elim_potentiated
        self.__threshold = threshold

    @property
    @overrides(AbstractElimination.vertex_executable_suffix)
    def vertex_executable_suffix(self):
        return "_weight"

    @overrides(AbstractElimination.get_parameters_sdram_usage_in_bytes)
    def get_parameters_sdram_usage_in_bytes(self):
        return 3 * 4

    @overrides(AbstractElimination.write_parameters)
    def write_parameters(self, spec, weight_scale):
        spec.write_value(int(self.__prob_elim_depressed * 0xFFFFFFFF))
        spec.write_value(int(self.__prob_elim_potentiated * 0xFFFFFFFF))
        spec.write_value(self.__threshold * weight_scale)

    @overrides(AbstractElimination.get_parameter_names)
    def get_parameter_names(self):
        return ["prob_elim_depressed", "prob_elim_potentiated", "threshold"]
