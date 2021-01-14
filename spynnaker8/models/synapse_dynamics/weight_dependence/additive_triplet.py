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
import logging
from spynnaker.pyNN.models.neuron.plasticity.stdp.weight_dependence import (
    WeightDependenceAdditiveTriplet as
    _BaseClass)
logger = logging.getLogger(__name__)


class WeightDependenceAdditiveTriplet(_BaseClass):
    # noinspection PyPep8Naming
    def __init__(
            self, w_min=0.0, w_max=1.0, A3_plus=0.01, A3_minus=0.01):
        r"""
        :param float w_min: :math:`w_\mathrm{min}`
        :param float w_max: :math:`w_\mathrm{max}`
        :param float A3_plus: :math:`A_3^+`
        :param float A3_minus: :math:`A_3^-`
        """
        super(WeightDependenceAdditiveTriplet, self).__init__(
            w_max=w_max, w_min=w_min, A3_plus=A3_plus, A3_minus=A3_minus)
        logger.warning(
            "please use spynnaker.pyNN.models.neuron.plasticity.stdp."
            "weight_dependence.WeightDependenceAdditiveTriplet instead")
