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

#ifndef _NEURON_RECORDING_H_
#define _NEURON_RECORDING_H_

#include <common/neuron-typedefs.h>
#include <bit_field.h>

// A struct of the different types of recorded data
// Note data is just bytes here but actual type is used on writing
typedef struct recording_values_t {
    uint32_t time;
    uint8_t data[];
} recording_values_t;


typedef struct bitfield_values_t {
    uint32_t n_words;
    uint32_t time;
    uint32_t bits[];
} bitfield_values_t;

#define BITFIELD_SIZE 0

//! The index to record each variable to for each neuron
extern uint8_t **neuron_recording_indexes;

//! The index to record each bitfield variable to for each neuron
extern uint8_t **bitfield_recording_indexes;

//! The number of variables that *can* be recorded not including bit fields
extern uint32_t n_recorded_vars;

//! The number of bitfield variables that can be recorded
extern uint32_t n_bitfield_vars;

//! The values of the recorded variables
extern recording_values_t **recording_values;

//! The values of the bitfield variables
extern bitfield_values_t **bitfield_values;

//! The size of the recording elements
extern uint32_t *var_recording_element_size;

//! \brief stores a recording of a value
//! \param[in] var_index: which recording variable to write this is
//! \param[in] neuron_index: the neuron id for this recorded data
//! \param[in] value: pointer to the value to record for this neuron.
static inline void neuron_recording_record_value(
        uint32_t var_index, uint32_t neuron_index, void *value) {
    uint32_t index = neuron_recording_indexes[var_index][neuron_index];
    uint32_t size = var_recording_element_size[var_index];
    uint32_t p = size * index;
    spin1_memcpy(&recording_values[var_index]->data[p], value, size);
}

//! \brief stores a recording of an accum variable
//! \param[in] var_index: which recording variable to write this is
//! \param[in] neuron_index: the neuron id for this recorded data
//! \param[in] value: the results to record for this neuron.
static inline void neuron_recording_record_accum(
        uint32_t var_index, uint32_t neuron_index, accum value) {
    uint8_t index = neuron_recording_indexes[var_index][neuron_index];
    accum *data = (accum *) &recording_values[var_index]->data;
    data[index] = value;
}

//! \brief stores a recording of a double variable
//! \param[in] var_index: which recording variable to write this is
//! \param[in] neuron_index: the neuron id for this recorded data
//! \param[in] value: the results to record for this neuron.
static inline void neuron_recording_record_double(
        uint32_t var_index, uint32_t neuron_index, double value) {
    uint8_t index = neuron_recording_indexes[var_index][neuron_index];
    double *data = (double *) &recording_values[var_index]->data;
    data[index] = value;
}

//! \brief stores a recording of a float variable
//! \param[in] var_index: which recording variable to write this is
//! \param[in] neuron_index: the neuron id for this recorded data
//! \param[in] value: the results to record for this neuron.
static inline void neuron_recording_record_float(
        uint32_t var_index, uint32_t neuron_index, float value) {
    uint8_t index = neuron_recording_indexes[var_index][neuron_index];
    float *data = (float *) &recording_values[var_index]->data;
    data[index] = value;
}

//! \brief stores a recording of an int32_t variable
//! \param[in] var_index: which recording variable to write this is
//! \param[in] neuron_index: the neuron id for this recorded data
//! \param[in] value: the results to record for this neuron.
static inline void neuron_recording_record_int32(
        uint32_t var_index, uint32_t neuron_index, int32_t value) {
    uint8_t index = neuron_recording_indexes[var_index][neuron_index];
    int32_t *data = (int32_t *) &recording_values[var_index]->data;
    data[index] = value;
}


//! \brief stores a recording of a set bit
//! \param[in] var_index: which bitfield recording variable to write this is
//! \param[in] neuron_index: which neuron to set the bit for
static inline void neuron_recording_record_bit(
        uint32_t var_index, uint32_t neuron_index) {
    // Record the bit
    uint32_t index = bitfield_recording_indexes[var_index][neuron_index];
    bit_field_set(bitfield_values[var_index]->bits, index);
}

//! \brief does the recording matrix process of handing over to basic recording
//! \param[in] time: the time stamp for this recording
void neuron_recording_record(uint32_t time);

//! \brief sets up state for next recording.
void neuron_recording_setup_for_next_recording(void);

//! \brief reads recording data from sdram on reset.
//! \param[in] n_neurons: the number of neurons to setup for
//! \return bool stating if the read was successful or not
bool neuron_recording_reset(uint32_t n_neurons);

//! \brief sets up the recording stuff
//! \param[in] recording_address: sdram location for the recording data
//! \param[out] recording_flags: Output of flags which can be used to check if
//!            a channel is enabled for recording
//! \param[in] n_neurons: the number of neurons to setup for
//! \return bool stating if the init was successful or not
bool neuron_recording_initialise(
        void *recording_address, uint32_t *recording_flags,
        uint32_t n_neurons);

//! \brief finishes recording
void neuron_recording_finalise(void);

#endif //_NEURON_RECORDING_H_
