/*
 * Copyright (c) 2017-2019 The University of Manchester
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program.  If not, see <http://www.gnu.org/licenses/>.
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
    RECORDING_REGION            //!< general recording data; 15
} regions_e;
