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

from spynnaker.pyNN.exceptions import SpynnakerException
from spynnaker.pyNN.models.defaults import defaults, default_initial_values


@defaults
class HHCondExp(object):
    """ Single-compartment Hodgkin-Huxley model with exponentially decaying \
        current input.

    .. warning::

        Not currently supported by the tool chain.
    """

    # noinspection PyPep8Naming
    @default_initial_values({"v", "gsyn_exc", "gsyn_inh"})
    def __init__(
            self, gbar_K=6.0, cm=0.2, e_rev_Na=50.0, tau_syn_E=0.2,
            tau_syn_I=2.0, i_offset=0.0, g_leak=0.01, e_rev_E=0.0,
            gbar_Na=20.0, e_rev_leak=-65.0, e_rev_I=-80, e_rev_K=-90.0,
            v_offset=-63, v=-65.0, gsyn_exc=0.0, gsyn_inh=0.0):
        # pylint: disable=unused-argument
        raise SpynnakerException(
            "This neuron model is currently not supported by the tool chain")
