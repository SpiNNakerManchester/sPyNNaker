/*
 * Copyright (c) 2019-2020 The University of Manchester
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
//! \brief Recording of the state of a neuron (spiking, voltage, etc.)

#ifndef _MEANFIELD_RECORDING_H_
#define _MEANFIELD_RECORDING_H_

#include <common/neuron-typedefs.h>
#include <bit_field.h>
#include <recording.h>
#include <wfi.h>

//#include "implementations/meanfield_impl_standard.h"


//! A struct of the different types of recorded data
// Note data is just bytes here but actual type is used on writing
typedef struct recording_values_t {
    uint32_t time;
    uint8_t data[];
} recording_values_t;

//! A struct for bitfield data
typedef struct bitfield_values_t {
    uint32_t time;
    uint32_t bits[];
} bitfield_values_t;

//! A struct for information for a non-bitfield recording
typedef struct recording_info_t {
    uint32_t element_size;
    uint32_t rate;
    uint32_t count;
    uint32_t increment;
    uint32_t size;
    recording_values_t *values;
} recording_info_t;

//! A struct for information on a bitfield recording
typedef struct bitfield_info_t {
    uint32_t rate;
    uint32_t count;
    uint32_t increment;
    uint32_t size;
    uint32_t n_words;
    bitfield_values_t *values;
} bitfield_info_t;

//! The index to record each variable to for each neuron
extern uint8_t **neuron_recording_indexes;

//! The index to record each bitfield variable to for each neuron
extern uint8_t **bitfield_recording_indexes;

//! An array of recording information structures
extern recording_info_t *recording_info;

//! An array of bitfield information structures
extern bitfield_info_t *bitfield_info;

//! An array of spaces into which recording values can be written
extern uint8_t **recording_values;

//! An array of spaces into which bitfields can be written
extern uint32_t **bitfield_values;

//! \brief stores a recording of a value of any type, except bitfield;
//!        use the functions below for common types as these will be faster.
//! \param[in] var_index: which recording variable to write this is
//! \param[in] neuron_index: the neuron id for this recorded data
//! \param[in] value: pointer to the value to record for this neuron.
static inline void neuron_recording_record_value(
        uint32_t var_index, uint32_t neuron_index, void *value) {
    uint32_t index = neuron_recording_indexes[var_index][neuron_index];
    uint32_t size = recording_info[var_index].element_size;
    uint32_t p = size * index;
    spin1_memcpy(&recording_values[var_index][p], value, size);
}

//! \brief stores a recording of an accum variable only; this is faster than
//!        neuron_recording_record_value for this type
//! \param[in] var_index: which recording variable to write this is
//! \param[in] neuron_index: the neuron id for this recorded data
//! \param[in] value: the results to record for this neuron.
static inline void neuron_recording_record_accum(
        uint32_t var_index, uint32_t neuron_index, accum value) {
    uint8_t index = neuron_recording_indexes[var_index][neuron_index];
    accum *data = (accum *) recording_values[var_index];
    data[index] = value;
}

//! \brief stores a recording of a double variable only; this is faster than
//!        neuron_recording_record_value for this type
//! \param[in] var_index: which recording variable to write this is
//! \param[in] neuron_index: the neuron id for this recorded data
//! \param[in] value: the results to record for this neuron.
static inline void neuron_recording_record_double(
        uint32_t var_index, uint32_t neuron_index, double value) {
    uint8_t index = neuron_recording_indexes[var_index][neuron_index];
    double *data = (double *) recording_values[var_index];
    data[index] = value;
}

//! \brief stores a recording of a float variable only; this is faster than
//!        neuron_recording_record_value for this type
//! \param[in] var_index: which recording variable to write this is
//! \param[in] neuron_index: the neuron id for this recorded data
//! \param[in] value: the results to record for this neuron.
static inline void neuron_recording_record_float(
        uint32_t var_index, uint32_t neuron_index, float value) {
    uint8_t index = neuron_recording_indexes[var_index][neuron_index];
    float *data = (float *) recording_values[var_index];
    data[index] = value;
}

//! \brief stores a recording of an int32_t variable only; this is faster than
//!        neuron_recording_record_value for this type
//! \param[in] var_index: which recording variable to write this is
//! \param[in] neuron_index: the neuron id for this recorded data
//! \param[in] value: the results to record for this neuron.
static inline void neuron_recording_record_int32(
        uint32_t var_index, uint32_t neuron_index, int32_t value) {
    uint8_t index = neuron_recording_indexes[var_index][neuron_index];
    int32_t *data = (int32_t *) recording_values[var_index];
    data[index] = value;
}


//! \brief stores a recording of a set bit; this is the only way to set a bit
//!        in a bitfield; neuron_recording_record_value doesn't work for this!
//! \param[in] var_index: which bitfield recording variable to write this is
//! \param[in] neuron_index: which neuron to set the bit for
static inline void neuron_recording_record_bit(
        uint32_t var_index, uint32_t neuron_index) {
    // Record the bit
    uint32_t index = neuron_recording_indexes[var_index][neuron_index];
    bit_field_set(bitfield_values[var_index], index);
}

//! \brief does the recording process of handing over to basic recording
//! \param[in] time: the time to put into the recording stamps.
static inline void neuron_recording_record(uint32_t time) {
    // go through all recordings
    for (uint32_t i = N_RECORDED_VARS; i > 0; i--) {
        recording_info_t *rec_info = &recording_info[i - 1];
        // if the rate says record, record now
        if (rec_info->count == rec_info->rate) {
            // Reset the count
            rec_info->count = 1;
            // Set the time and record the data
            rec_info->values->time = time;
            recording_record(i - 1, rec_info->values, rec_info->size);
        } else {

            // Not recording this time, so increment by specified amount
            rec_info->count += rec_info->increment;
        }
    }

    for (uint32_t i = N_BITFIELD_VARS; i > 0; i--) {
        bitfield_info_t *bf_info = &bitfield_info[i - 1];
        // if the rate says record, record now
        if (bf_info->count == bf_info->rate) {
            // Reset the count
            bf_info->count = 1;
            // Skip empty bitfields
            if (empty_bit_field(bf_info->values->bits, bf_info->n_words)) {
                continue;
            }
            // Set the time and record the data (note index is after recorded_vars)
            bf_info->values->time = time;
            recording_record(i + N_RECORDED_VARS - 1, bf_info->values, bf_info->size);
        } else {

            // Not recording this time, so increment by specified amount
            bf_info->count += bf_info->increment;
        }
    }
}

//! \brief sets up state for next recording.
static inline void neuron_recording_setup_for_next_recording(void) {
    // Reset the bitfields before starting if a beginning of recording
    for (uint32_t i = N_BITFIELD_VARS; i > 0; i--) {
        bitfield_info_t *b_info = &bitfield_info[i - 1];
        if (b_info->count == 1) {
            clear_bit_field(b_info->values->bits, b_info->n_words);
        }
    }
}

//! \brief reads recording data from sdram on reset.
//! \param[in] n_neurons: the number of neurons to setup for
//! \return bool stating if the read was successful or not
bool neuron_recording_reset(uint32_t n_neurons);

//! \brief sets up the recording stuff
//! \param[in] recording_address: sdram location for the recording data
//! \param[out] recording_flags: Output of flags which can be used to check if
//!            a channel is enabled for recording
//! \param[in] n_neurons: the number of neurons to setup for
//! \param[out] n_rec_regions_used: Output the number of regions used by neuron
//!            recording
//! \return bool stating if the init was successful or not
bool neuron_recording_initialise(
        void *recording_address, uint32_t *recording_flags,
        uint32_t n_neurons, uint32_t *n_rec_regions_used);

//! \brief finishes recording
void neuron_recording_finalise(void);

#endif //_NEURON_RECORDING_H_
