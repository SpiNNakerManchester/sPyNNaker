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
#include <recording.h>

// declare spin1_wfi
void spin1_wfi();

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

//! The number of recordings outstanding
extern uint32_t n_recordings_outstanding;

//! The size of an element of recording
extern uint32_t *var_recording_element_size;

//! The number of time steps between each variable recording
extern uint32_t *var_recording_rate;

//! Count of time steps until next variable recording
extern uint32_t *var_recording_count;

//! Increment of count until next variable recording
//! - 0 if not recorded, 1 if recorded
extern uint32_t *var_recording_increment;

//! The size of the recorded variables in bytes for a time step
extern uint32_t *var_recording_size;

//! The number of time steps between each variable recording
extern uint32_t *bitfield_recording_rate;

//! Count of time steps until next variable recording
extern uint32_t *bitfield_recording_count;

//! Increment of count until next variable recording
//! - 0 if not recorded, 1 if recorded
extern uint32_t *bitfield_recording_increment;

//! The size of the recorded variables in bytes for a time step
extern uint32_t *bitfield_recording_size;

//! \brief function to handle when a recording stage finished
static void recording_done_callback(void) {
    n_recordings_outstanding -= 1;
}

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

//! \brief does the recording process of handing over to basic recording
//! \param[in] time: the time to put into the recording stamps.
static inline void neuron_recording_record(uint32_t time) {
    // go through all recordings
    //uint32_t s = tc[T1_COUNT];
    for (uint32_t i = 0; i < n_recorded_vars; i++) {
        // if the rate says record, record now
        if (var_recording_count[i] == var_recording_rate[i]) {
            // Reset the count
            var_recording_count[i] = 1;
            // Note we are recording
            n_recordings_outstanding += 1;
            // Set the time and record the data
            recording_values[i]->time = time;
            recording_record_and_notify(
                i, recording_values[i], var_recording_size[i],
                recording_done_callback);
        } else {

            // Not recording this time, so increment by specified amount
            var_recording_count[i] += var_recording_increment[i];
        }
    }

    for (uint32_t i = 0; i < n_bitfield_vars; i++) {
        // if the rate says record, record now
        if (bitfield_recording_count[i] == bitfield_recording_rate[i]) {
            // Reset the count
            bitfield_recording_count[i] = 1;
            // Skip empty bitfields
            if (empty_bit_field(bitfield_values[i]->bits, bitfield_values[i]->n_words)) {
                continue;
            }
            // Note we are recording
            n_recordings_outstanding += 1;
            // Set the time and record the data (note index is after recorded_vars)
            bitfield_values[i]->time = time;
            recording_record_and_notify(
                i + n_recorded_vars, &bitfield_values[i]->time,
                bitfield_recording_size[i], recording_done_callback);
        } else {

            // Not recording this time, so increment by specified amount
            bitfield_recording_count[i] += bitfield_recording_increment[i];
        }
    }
    //uint32_t e = tc[T1_COUNT];
    //log_info("nr: %u", s-e);
    recording_do_timestep_update(time);
}

//! \brief sets up state for next recording.
static void neuron_recording_setup_for_next_recording(void) {
    // Wait until recordings have completed, to ensure the recording space
    // can be re-written
    while (n_recordings_outstanding > 0) {
       spin1_wfi();
    }

    // Reset the bitfields before starting if a beginning of recording
    for (uint32_t i = 0; i < n_bitfield_vars; i++) {
        if (bitfield_recording_rate[i] == 1) {
            clear_bit_field(bitfield_values[i]->bits, bitfield_values[i]->n_words);
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
//! \return bool stating if the init was successful or not
bool neuron_recording_initialise(
        void *recording_address, uint32_t *recording_flags,
        uint32_t n_neurons);

//! \brief finishes recording
void neuron_recording_finalise(void);

#endif //_NEURON_RECORDING_H_
