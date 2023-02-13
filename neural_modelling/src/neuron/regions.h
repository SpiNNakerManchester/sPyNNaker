/*
 * Copyright (c) 2017-2023 The University of Manchester
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

//! \file
//! \brief Standard layout of DSG regions in neuron code.
//!
//! Note that not all models use all of these regions, but they all use the same
//! region identifier mapping.
#pragma once

//! DSG region identifiers
typedef enum neuron_regions_e {
    SYSTEM_REGION,              //!< simulation system; 0
    CORE_PARAMS_REGION,         //!< core parameters; 1
    NEURON_PARAMS_REGION,       //!< neuron parameters; 2
    CURRENT_SOURCE_PARAMS_REGION, //!< current source parameters; 3
    SYNAPSE_PARAMS_REGION,      //!< synapse parameters; 4
    POPULATION_TABLE_REGION,    //!< master population table; 5
    SYNAPTIC_MATRIX_REGION,     //!< synaptic matrix; 6
    SYNAPSE_DYNAMICS_REGION,    //!< synapse dynamics; 7
    STRUCTURAL_DYNAMICS_REGION, //!< structural dynamics; 8
    NEURON_RECORDING_REGION,    //!< recording; 9
    PROVENANCE_DATA_REGION,     //!< provenance; 10
    PROFILER_REGION,            //!< profiling; 11
    CONNECTOR_BUILDER_REGION,   //!< connection building; 12
    NEURON_BUILDER_REGION,      //!< neuron building; 13
    BIT_FIELD_FILTER_REGION,    //!< bitfield filter; 14
    RECORDING_REGION,           //!< general recording data; 15
	INITIAL_VALUES_REGION       //!< initial neuron state; 16
} regions_e;
