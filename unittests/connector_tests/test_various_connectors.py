# Copyright (c) 2027 The University of Manchester
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import inspect
import tempfile
from typing import Any, Dict, List, Tuple
import unittest

import csa
import numpy
from pyNN.random import NumpyRNG

from spynnaker.pyNN.models.neural_projections.connectors import (
    AbstractConnector, AllButMeConnector, AllToAllConnector, ArrayConnector,
    ConvolutionConnector, CSAConnector, DistanceDependentProbabilityConnector,
    FixedNumberPostConnector, FixedNumberPreConnector,
    FixedProbabilityConnector, FromFileConnector, FromListConnector,
    IndexBasedProbabilityConnector, KernelConnector, MultapseConnector,
    OneToOneConnector, OneToOneOffsetConnector, PoolDenseConnector,
    SmallWorldConnector)


class TestConnectors(unittest.TestCase):

    def compare_values(self, key: str, value1: Any, value2: Any) -> None:
        if isinstance(value1, numpy.ndarray):
            numpy.testing.assert_array_equal(value1, value2)
        else:
            self.assertEqual(value1, value2, key)

    def compare_connectors(self, connector: AbstractConnector,
                           connector2: AbstractConnector) -> None:
        """
        ultra pythonic way of comparing two connectors

        Just enough to pass these tests
        """
        members = inspect.getmembers(connector)
        members2 = inspect.getmembers(connector2)
        for (key1, value1), (key2, value2) in zip(members, members2):
            if key1 != key2:
                raise AssertionError(f"{key1=}, {key2=}")
            if key1.startswith("__") and key2.endswith("__"):
                pass
            elif inspect.ismethod(value1):
                pass
            elif inspect.isfunction(value1):
                pass
            else:
                self.compare_values(key1, value1, value2)

    def compare_parameters(
            self, params: Dict[str, Any], params2: Dict[str, Any]) -> None:
        assert len(params) == len(params2)
        for key in params:
            self.compare_values(key, params[key], params2[key])

    def testOneToOneConnector_defaults(self) -> None:
        connector = OneToOneConnector()
        params = connector.get_parameters()
        connector2 = OneToOneConnector(**params)
        assert connector2.get_parameters() == params
        self.compare_connectors(connector, connector2)
        connector3 = connector.clone()
        self.compare_connectors(connector, connector3)
        connector.describe()

    def testOneToOneConnector_not_defaults(self) -> None:
        connector = OneToOneConnector(safe=False, verbose=True)
        params = connector.get_parameters()
        connector2 = OneToOneConnector(**params)
        assert connector2.get_parameters() == params
        assert connector2.safe is False
        assert connector2.verbose is True
        # Callback is not interesting
        self.compare_connectors(connector, connector2)
        connector3 = connector.clone()
        self.compare_connectors(connector, connector3)

    def testAllButMeConnector(self) -> None:
        weights = numpy.ones((2, 2))
        connector = AllButMeConnector(n_neurons_per_group=2, weights=weights)
        params = connector.get_parameters()
        connector2 = AllButMeConnector(**params)
        assert connector2.get_parameters() == params
        self.compare_connectors(connector, connector2)
        connector3 = connector.clone()
        self.compare_connectors(connector, connector3)

    def testAllToAllConnector(self) -> None:
        connector = AllToAllConnector(allow_self_connections=False)
        params = connector.get_parameters()
        connector2 = AllToAllConnector(**params)
        assert connector2.get_parameters() == params
        assert connector2.allow_self_connections is False
        self.compare_connectors(connector, connector2)
        connector3 = connector.clone()
        self.compare_connectors(connector, connector3)

    def testArrayConnector(self) -> None:
        array = numpy.array([[1, 2, 3], [4, 5, 6]])
        connector = ArrayConnector(array)
        params = connector.get_parameters()
        connector2 = ArrayConnector(**params)
        assert connector2.get_parameters() == params
        self.compare_connectors(connector, connector2)
        connector3 = connector.clone()
        self.compare_connectors(connector, connector3)

    def testFixedNumberPostConnector(self) -> None:
        rng = NumpyRNG(seed=42)
        connector = FixedNumberPostConnector(
            5, allow_self_connections=False, with_replacement=True,
            rng=rng)
        params = connector.get_parameters()
        connector2 = FixedNumberPostConnector(**params)
        assert connector2.get_parameters() == params
        assert connector2.allow_self_connections is False
        self.compare_connectors(connector, connector2)
        connector3 = connector.clone()
        self.compare_connectors(connector, connector3)

    def testFixedNumberPreConnector(self) -> None:
        rng = NumpyRNG(seed=14)
        connector = FixedNumberPreConnector(
            7, allow_self_connections=False, with_replacement=True,
            rng=rng)
        params = connector.get_parameters()
        connector2 = FixedNumberPreConnector(**params)
        assert connector2.get_parameters() == params
        assert connector2.allow_self_connections is False
        self.compare_connectors(connector, connector2)
        connector3 = connector.clone()
        self.compare_connectors(connector, connector3)

    def testFixedProbabilityConnectorr(self) -> None:
        rng = NumpyRNG(seed=14)
        connector = FixedProbabilityConnector(
            0.5, allow_self_connections=False, rng=rng)
        params = connector.get_parameters()
        connector2 = FixedProbabilityConnector(**params)
        assert connector2.get_parameters() == params
        assert connector2.p_connect == 0.5
        self.compare_connectors(connector, connector2)
        connector3 = connector.clone()
        self.compare_connectors(connector, connector3)

    def testKernelConnector(self) -> None:
        (psh, psw, ksh, ksw) = (32, 16, 3, 3)
        shape_pre = [psh, psw]
        shape_post = [psh // 2, psw // 2]
        shape_kernel = [ksh, ksw]
        weight_list = [[7.0 if ((a + b) % 2 == 0) else 5.0
                        for a in range(ksw)] for b in range(ksh)]
        delay_list = [[20.0 if ((a + b) % 2 == 1) else 10.0
                       for a in range(ksw)] for b in range(ksh)]
        weight_kernel = numpy.asarray(weight_list)
        pre_step = (1, 1)
        post_step = (1, 1)
        pre_start = (0, 0)
        post_start = (0, 0)
        connector = KernelConnector(
                shape_pre, shape_post, shape_kernel,
                weight_kernel=weight_kernel, delay_kernel=delay_list,
                pre_sample_steps_in_post=pre_step,
                post_sample_steps_in_pre=post_step,
                pre_start_coords_in_post=pre_start,
                post_start_coords_in_pre=post_start)
        params = connector.get_parameters()
        connector2 = KernelConnector(**params)
        params2 = connector2.get_parameters()
        self.compare_parameters(params, params2)
        self.compare_connectors(connector, connector2)
        connector3 = connector.clone()
        self.compare_connectors(connector, connector3)

    def testMultapseConnector(self) -> None:
        rng = NumpyRNG(seed=37)
        connector = MultapseConnector(
            4, allow_self_connections=False, with_replacement=False,
            rng=rng)
        params = connector.get_parameters()
        connector2 = MultapseConnector(**params)
        assert connector2.get_parameters() == params
        self.compare_connectors(connector, connector2)
        connector3 = connector.clone()
        self.compare_connectors(connector, connector3)

    def testOneToOneOffsetConnector(self) -> None:
        connector = OneToOneOffsetConnector(
            offset=5, wrap=True, n_neurons_per_group=4)
        params = connector.get_parameters()
        connector2 = OneToOneOffsetConnector(**params)
        assert connector2.get_parameters() == params
        self.compare_connectors(connector, connector2)
        connector3 = connector.clone()
        self.compare_connectors(connector, connector3)

    def testConvolutionConnectorDefaults(self) -> None:
        k_shape = numpy.array([5, 5], dtype='int32')
        kernel = (numpy.arange(numpy.prod(
            k_shape)) - (numpy.prod(k_shape) / 2)).reshape(k_shape) * 0.1
        connector = ConvolutionConnector(kernel)
        params = connector.get_parameters()
        connector2 = ConvolutionConnector(**params)
        self.compare_parameters(params, connector2.get_parameters())
        self.compare_connectors(connector, connector2)
        connector3 = connector.clone()
        self.compare_connectors(connector, connector3)

    def testConvolutionConnectorWeird(self) -> None:
        # WARNING the values used here are NOT good use case examples
        # They are purely random values to pass in and out
        k_shape = (5, 5)
        kernel = (numpy.arange(numpy.prod(
            k_shape)) - (numpy.prod(k_shape) / 2)).reshape(k_shape) * 0.1
        strides = (3, 3)
        connector = ConvolutionConnector(
            kernel_weights=kernel, kernel_shape=(5, 5), strides=strides,
            padding=(2, 3), pool_shape=(4, 5), pool_stride=(4, 3),
            positive_receptor_type="gigo1", negative_receptor_type="gigo2",
            filter_edges=False)
        params = connector.get_parameters()
        connector2 = ConvolutionConnector(**params)
        self.compare_parameters(params, connector2.get_parameters())
        self.compare_connectors(connector, connector2)
        connector3 = connector.clone()
        self.compare_connectors(connector, connector3)
        # Remember values used here NOT examples

    def testCSAConnector(self) -> None:
        connector = CSAConnector(csa.oneToOne)
        params = connector.get_parameters()
        connector2 = CSAConnector(**params)
        self.compare_parameters(params, connector2.get_parameters())
        self.compare_connectors(connector, connector2)
        connector3 = connector.clone()
        self.compare_connectors(connector, connector3)

    def testDistanceDependentProbabilityConnector(self) -> None:
        rng = NumpyRNG(seed=14)
        connector = DistanceDependentProbabilityConnector(
            d_expression="gigo", allow_self_connections=False,
            n_connections=None, rng=rng)
        params = connector.get_parameters()
        connector2 = DistanceDependentProbabilityConnector(**params)
        assert connector2.get_parameters() == params
        self.compare_connectors(connector, connector2)
        connector3 = connector.clone()
        self.compare_connectors(connector, connector3)

    def testFromListConnectorrSimple(self) -> None:
        from_list: List[Tuple[int, ...]] = [(1, 2), (3, 4), (5, 6)]
        connector = FromListConnector(from_list)
        params = connector.get_parameters()
        connector2 = FromListConnector(**params)
        self.compare_parameters(params, connector2.get_parameters())
        self.compare_connectors(connector, connector2)
        connector3 = connector.clone()
        self.compare_connectors(connector, connector3)

    def testFromListConnectorrNamed(self) -> None:
        from_list: List[Tuple[int, ...]] = [(1, 2, 3), (4, 5, 6)]
        connector = FromListConnector(from_list, ["weight"])
        params = connector.get_parameters()
        connector2 = FromListConnector(**params)
        self.compare_parameters(params, connector2.get_parameters())
        self.compare_connectors(connector, connector2)
        connector3 = connector.clone()
        self.compare_connectors(connector, connector3)

    def testFromFileConnector(self) -> None:
        as_list = [(0, 0), (13, 0), (2, 13), (5, 1), (0, 1)]
        _, name = tempfile.mkstemp(".temp")
        numpy.savetxt(name, as_list)

        connector = FromFileConnector(name)
        params = connector.get_parameters()
        # FromFileConnector return FromListConnector Params
        connector2 = FromListConnector(**params)
        self.compare_parameters(params, connector2.get_parameters())
        self.compare_values(
            "conn_list", connector.conn_list, connector2.conn_list)
        # FromFileConnector clone returns a FromListConnector
        connector3 = connector.clone()
        self.compare_values(
            "conn_list", connector.conn_list, connector3.conn_list)

    def testIndexBasedProbabilityConnector(self) -> None:
        rng = NumpyRNG(seed=14)
        connector = IndexBasedProbabilityConnector(
            index_expression="gigo", allow_self_connections=False,
            rng=rng)
        params = connector.get_parameters()
        connector2 = IndexBasedProbabilityConnector(**params)
        assert connector2.get_parameters() == params
        self.compare_connectors(connector, connector2)
        connector3 = connector.clone()
        self.compare_connectors(connector, connector3)

    def testPoolDenseConnector(self) -> None:
        # WARNING the values used here are NOT good use case examples
        # They are purely random values to pass in and out
        shape = 1
        stride = 2
        connector = PoolDenseConnector(
            [0, 200, 0], shape, stride, "gigo1", "gigo2")
        params = connector.get_parameters()
        connector2 = PoolDenseConnector(**params)
        self.compare_parameters(params, connector2.get_parameters())
        self.compare_connectors(connector, connector2)
        connector3 = connector.clone()
        self.compare_connectors(connector, connector3)
        # Remember values used here NOT examples

    def testSmallWorldConnector(self) -> None:
        # WARNING the values used here are NOT good use case examples
        # They are purely random values to pass in and out
        rng = NumpyRNG(seed=13)
        connector = SmallWorldConnector(1.2, 3.4, True, None, rng)
        params = connector.get_parameters()
        connector2 = SmallWorldConnector(**params)
        self.compare_parameters(params, connector2.get_parameters())
        self.compare_connectors(connector, connector2)
        connector3 = connector.clone()
        self.compare_connectors(connector, connector3)
        # Remember values used here NOT examples
