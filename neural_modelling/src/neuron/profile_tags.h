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

// Profiler tags
#pragma once

enum profiler_tags_e {
    PROFILER_TIMER,                     // 0
    PROFILER_DMA_READ,                  // 1
    PROFILER_INCOMING_SPIKE,            // 2
    PROFILER_PROCESS_FIXED_SYNAPSES,    // 3
    PROFILER_PROCESS_PLASTIC_SYNAPSES   // 4
};
