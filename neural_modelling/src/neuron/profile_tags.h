/*
 * Copyright (c) 2017 The University of Manchester
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     https://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

//! \file
//! \brief Profiler tags
#pragma once

//! Tags used when profiling sPyNNaker neuron code
enum profiler_tags_e {
    PROFILER_TIMER,                     //!< timer
    PROFILER_DMA_READ,                  //!< DMA read
    PROFILER_INCOMING_SPIKE,            //!< incoming spike handling
    PROFILER_PROCESS_FIXED_SYNAPSES,    //!< fixed synapse processing
    PROFILER_PROCESS_PLASTIC_SYNAPSES   //!< plastic synapse processing
};
