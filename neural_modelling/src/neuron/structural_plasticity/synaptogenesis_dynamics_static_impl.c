/*
 * Copyright (c) 2016-2023 The University of Manchester
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

/*!
 * \file
 * \brief This file contains the static (non-)implementation of synaptogenesis.
 * \details No functionality is gained with this class.
 */
#include "synaptogenesis_dynamics.h"
#include <debug.h>

bool synaptogenesis_dynamics_initialise(
        UNUSED address_t sdram_sp_address, uint32_t *recording_regions_used) {
    // The recording region is defined even if unused, so this value needs to
    // be incremented in order for the recording region IDs to match up
    *recording_regions_used += 1;
    return true;
}

bool synaptogenesis_dynamics_rewire(
        UNUSED uint32_t time, UNUSED spike_t *spike,
        UNUSED pop_table_lookup_result_t *result) {
    return false;
}

bool synaptogenesis_row_restructure(
        UNUSED uint32_t time, UNUSED synaptic_row_t row) {
    return false;
}

void synaptogenesis_spike_received(UNUSED uint32_t time, UNUSED spike_t spike) {
}

uint32_t synaptogenesis_n_updates(void) {
    return 0;
}

void print_post_to_pre_entry(void) {
    return;
}
