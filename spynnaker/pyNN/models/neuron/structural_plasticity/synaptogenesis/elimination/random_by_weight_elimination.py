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

from .abstract_elimination import AbstractElimination
from pacman.model.decorators.overrides import overrides


class RandomByWeightElimination(AbstractElimination):
    """ Elimination Rule that depends on the weight of a synapse
    """

    __slots__ = [
        "__prob_elim_depression",
        "__prob_elim_potentiation",
        "__mid_weight"
    ]

    def __init__(
            self, mid_weight, prob_elim_depression=0.0245,
            prob_elim_potentiation=1.36 * 10 ** -4):
        """

        :param mid_weight:\
            Below this weight is considered depression, above or equal to this\
            weight is considered potentiation (or the static weight of the\
            connection on static weight connections)
        :param prob_elim_depression:\
            The probability of elimination if the weight has been depressed\
            (ignored on static weight connections)
        :param prob_elim_potentiation:\
            The probability of elimination of the weight has been potentiated\
            or has not changed (and also used on static weight connections)
        """
        self.__prob_elim_depression = prob_elim_depression
        self.__prob_elim_potentiation = prob_elim_potentiation
        self.__mid_weight = mid_weight

    @property
    @overrides(AbstractElimination.vertex_executable_suffix)
    def vertex_executable_suffix(self):
        return "_weight"

    @overrides(AbstractElimination.get_parameters_sdram_usage_in_bytes)
    def get_parameters_sdram_usage_in_bytes(self):
        return 3 * 4

    @overrides(AbstractElimination.write_parameters)
    def write_parameters(self, spec):
        spec.write_value(self.__prob_elim_depression)
        spec.write_value(self.__prob_elim_potentiation)
        spec.write_value(self.__mid_weight)

    @overrides(AbstractElimination.get_parameter_names)
    def get_parameter_names(self):
        return ["prob_elim_depression", "prob_elim_potentiation", "mid_weight"]
