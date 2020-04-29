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
    SYSTEM_REGION,            //!< simulation system; 0
    NEURON_PARAMS_REGION,     //!< neuron parameters; 1
    SYNAPSE_PARAMS_REGION,    //!< synapse parameters; 2
    POPULATION_TABLE_REGION,  //!< master population table; 3
    SYNAPTIC_MATRIX_REGION,   //!< synaptic matrix; 4
    SYNAPSE_DYNAMICS_REGION,  //!< synapse dynamics; 5
    NEURON_RECORDING_REGION,  //!< recording; 6
    PROVENANCE_DATA_REGION,   //!< provenance; 7
    PROFILER_REGION,          //!< profiling; 8
    CONNECTOR_BUILDER_REGION, //!< connection building; 9
    DIRECT_MATRIX_REGION      //!< direct synaptic matrix; 10
} regions_e;
