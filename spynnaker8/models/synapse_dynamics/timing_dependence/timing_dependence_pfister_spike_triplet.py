# Copyright (c) 2021 The University of Manchester
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
from spinn_utilities.log import FormatAdapter
from spynnaker.pyNN.models.neuron.plasticity.stdp.timing_dependence import (
    TimingDependencePfisterSpikeTriplet as
    _BaseClass)
logger = FormatAdapter(logging.getLogger(__name__))


class TimingDependencePfisterSpikeTriplet(_BaseClass):
    """
    .. deprecated:: 6.0
        Use
        :py:class:`spynnaker.pyNN.models.neuron.plasticity.stdp.timing_dependence.TimingDependencePfisterSpikeTriplet`
        instead.
    """
    __slots__ = []

    # noinspection PyPep8Naming
    def __init__(
            self, tau_plus, tau_minus, tau_x, tau_y, A_plus=0.01,
            A_minus=0.01):
        r"""
        :param float tau_plus: :math:`\tau_+`
        :param float tau_minus: :math:`\tau_-`
        :param float tau_x: :math:`\tau_x`
        :param float tau_y: :math:`\tau_y`
        :param float A_plus: :math:`A^+`
        :param float A_minus: :math:`A^-`
        """
        # pylint: disable=too-many-arguments
        super(TimingDependencePfisterSpikeTriplet, self).__init__(
            tau_plus=tau_plus, tau_minus=tau_minus, tau_x=tau_x,
            tau_y=tau_y, A_plus=A_plus, A_minus=A_minus)
        logger.warning(
            "please use spynnaker.pyNN.models.neuron.plasticity.stdp."
            "timing_dependence.TimingDependencePfisterSpikeTriplet instead")
