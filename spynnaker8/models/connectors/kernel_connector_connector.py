# Copyright (c) 2017-2021 The University of Manchester
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
from spynnaker.pyNN.models.neural_projections.connectors import (
    KernelConnector as
    _BaseClass)
from spynnaker.pyNN.utilities.utility_calls import moved_in_v6


class KernelConnector(_BaseClass):
    """
    Where the pre- and post-synaptic populations are considered as a 2D array.\
    Connect every post(row, col) neuron to many pre(row, col, kernel) through\
    a (kernel) set of weights and/or delays.

    .. deprecated:: 6.0
        Use
        :py:class:`spynnaker.pyNN.models.neural_projections.connectors.KernelConnector`
        instead.
    """
    __slots__ = []

    def __init__(
            self, shape_pre, shape_post, shape_kernel, weight_kernel=None,
            delay_kernel=None, shape_common=None,
            pre_sample_steps_in_post=None, pre_start_coords_in_post=None,
            post_sample_steps_in_pre=None, post_start_coords_in_pre=None,
            safe=True, space=None, verbose=False, callback=None):
        r"""
        :param tuple(int,int) shape_pre:
            2D shape of the pre population (rows/height, cols/width, usually
            the input image shape)
        :param tuple(int,int) shape_post:
            2D shape of the post population (rows/height, cols/width)
        :param tuple(int,int) shape_kernel:
            2D shape of the kernel (rows/height, cols/width)
        :param weight_kernel: (optional)
            2D matrix of size shape_kernel describing the weights
        :type weight_kernel: ~numpy.ndarray or ~pyNN.random.NumpyRNG
            or int or float or list(int) or list(float) or None
        :param delay_kernel: (optional)
            2D matrix of size shape_kernel describing the delays
        :type delay_kernel: ~numpy.ndarray or ~pyNN.random.NumpyRNG
            or int or float or list(int) or list(float) or None
        :param tuple(int,int) shape_common: (optional)
            2D shape of common coordinate system (for both pre and post,
            usually the input image sizes)
        :param tuple(int,int) pre_sample_steps_in_post: (optional)
            Sampling steps/jumps for pre pop :math:`\Leftrightarrow`
            :math:`(\mathsf{step}_x, \mathsf{step}_y)`
        :param tuple(int,int) pre_start_coords_in_post: (optional)
            Starting row/col for pre sampling :math:`\Leftrightarrow`
            :math:`(\mathsf{offset}_x, \mathsf{offset}_y)`
        :param tuple(int,int) post_sample_steps_in_pre: (optional)
            Sampling steps/jumps for post pop :math:`\Leftrightarrow`
            :math:`(\mathsf{step}_x, \mathsf{step}_y)`
        :param tuple(int,int) post_start_coords_in_pre: (optional)
            Starting row/col for post sampling :math:`\Leftrightarrow`
            :math:`(\mathsf{offset}_x, \mathsf{offset}_y)`
        :param bool safe:
            Whether to check that weights and delays have valid values. If
            False, this check is skipped.
        :param ~pyNN.space.Space space:
            Currently ignored; for future compatibility.
        :param bool verbose:
            Whether to output extra information about the connectivity to a
            CSV file
        :param callable callback: (ignored)
        """
        # pylint: disable=too-many-arguments
        moved_in_v6("spynnaker8.models.connectors.KernelConnector",
                    "spynnaker.pyNN.models.neural_projections.connectors"
                    ".KernelConnector")
        super(KernelConnector, self).__init__(
            shape_pre, shape_post, shape_kernel, weight_kernel,
            delay_kernel, shape_common, pre_sample_steps_in_post,
            pre_start_coords_in_post, post_sample_steps_in_pre,
            post_start_coords_in_pre, safe=safe, space=space, verbose=verbose,
            callback=callback)
