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

#include "neuron_recording.h"
#include "recording.h"
#include <common/out_spikes.h>
#include <bit_field.h>
#include  <stddef.h>

// declare spin1_wfi
void spin1_wfi();

//! Number of time steps between spike recordings
static uint32_t spike_recording_rate;

//! Number of neurons recording spikes
static uint32_t n_spike_recording_words;

//! Count of time steps until next spike recording
static uint32_t spike_recording_count;

//! Increment of count until next spike recording
//! - 0 if not recorded, 1 if recorded
static uint32_t spike_recording_increment;

//! The index to record each spike to for each neuron
static uint8_t *spike_recording_indexes;

//! The number of variables that *can* be recorded - might not be enabled
static uint32_t n_recorded_vars;

//! The number of time steps between each variable recording
static uint32_t *var_recording_rate;

//! The type index which states which state struct to use
static uint32_t *var_recording_type_index;

//! Count of time steps until next variable recording
static uint32_t *var_recording_count;

//! Increment of count until next variable recording
//! - 0 if not recorded, 1 if recorded
static uint32_t *var_recording_increment;

//! The index to record each variable to for each neuron
static uint8_t **var_recording_indexes;

//! The values of the recorded variables
static timed_state_t **var_recording_values;

//! The values for the recorded variables for doubles
static double_timed_state_t **var_double_recording_values;

//! The values for the recorded variables for floats
static float_timed_state_t **var_float_recording_values;

//! The size of the recorded variables in bytes for a time step
static uint32_t *var_recording_size;

//! The number of recordings outstanding
static uint32_t n_recordings_outstanding = 0;

// how many words read by the basic recording
static uint32_t basic_recording_words_read = 0;

#define TIME_STAMP_SIZE_IN_BYTES sizeof(uint32_t)

typedef enum recording_type_enum {
    NOT_MATRIX = 0,
    INT32 = 1,
    DOUBLE = 2,
    FLOAT = 3
} recording_type_enum;


//! \brief function to handle when a recording stage finished
void _recording_done_callback(void) {
    n_recordings_outstanding -= 1;
}

//! \brief returns how many variables are able to be recorded
//! \return the number of recordable variables
uint32_t neuron_recording_get_n_recorded_vars(void){
    return n_recorded_vars;
}

//! \brief allows neurons to wait till recordings have completed
void neuron_recording_wait_to_complete(void){
     // Wait until recordings have completed, to ensure the recording space
    // can be re-written
    while (n_recordings_outstanding > 0) {
        spin1_wfi();
    }
}

//! \brief stores a recording of a matrix based variable
//! \param[in] recording_var_index: which recording variable to write this is
//! \param[in] neuron_index: which neuron to set the spike for
//! \param[in] value: the data to store
void neuron_recording_set_recorded_param(
        uint32_t recording_var_index, uint32_t neuron_index, state_t value){
    uint32_t index = var_recording_indexes[
        recording_var_index + 1][neuron_index];
    var_recording_values[recording_var_index + 1]->states[index] = value;
}

void neuron_recorder_print_var_recording_indexes(
        uint32_t region, uint32_t n_neurons){
    for (uint32_t index_index = 0; index_index < n_neurons; index_index++){
        uint32_t index_value =
            (uint32_t) var_recording_indexes[region][index_index];
        log_info(
            "index value for neuron %d is %d", index_index, index_value);
    }
}

//! \brief stores a double recording of a matrix based variable
//! \param[in] recording_var_index: which recording variable to write this is
//! \param[in] neuron_index: which neuron to set the spike for
//! \param[in] value: the data to store
void neuron_recording_set_double_recorded_param(
        uint32_t recording_var_index, uint32_t neuron_index, double value){
    uint8_t index = var_recording_indexes[recording_var_index][neuron_index];
    uint32_t index_index = (uint32_t) index;
    var_double_recording_values[recording_var_index]->states[index] = value;
        log_debug(
        " double param at n i %d is at i %d and is %F",
        neuron_index, index_index, value);
}

//! \brief stores a double recording of a matrix based variable
//! \param[in] recording_var_index: which recording variable to write this is
//! \param[in] neuron_index: which neuron to set the spike for
//! \param[in] value: the data to store
void neuron_recording_set_float_recorded_param(
        uint32_t recording_var_index, uint32_t neuron_index, float value){
    uint32_t index = var_recording_indexes[recording_var_index][neuron_index];
    var_float_recording_values[recording_var_index]->states[index] = value;
    log_debug(" float param at n i %d is at i %d and is %f",
        neuron_index, index, value);
}

//! \brief stores a recording of a bitfield based variable
void neuron_recording_set_spike(uint32_t neuron_index){
    // Record the spike
    out_spikes_set_spike(spike_recording_indexes[neuron_index]);
}

//! \brief does the recording process of handing over to basic recording
void neuron_recording_matrix_record(uint32_t time) {
    for (uint32_t i = 1; i < n_recorded_vars + 1; i++) {
        log_debug(
            "%d count %d rate %d",
            i, var_recording_count[i], var_recording_rate[i]);
        if (var_recording_count[i] == var_recording_rate[i]) {
            var_recording_count[i] = 1;
            n_recordings_outstanding += 1;
            if (var_recording_type_index[i] == INT32) {
                var_recording_values[i]->time = time;
                recording_record_and_notify(
                    i, var_recording_values[i], var_recording_size[i],
                    _recording_done_callback);
                log_debug("recording %u bytes", var_recording_size[i]);
            } else if (var_recording_type_index[i] == DOUBLE){
                var_double_recording_values[i]->time = time;
                for(uint32_t data_i = 0;
                        data_i < var_recording_size[i] / sizeof(double);
                        data_i++){
                    log_debug("double data %d is %F and %x, %x",
                     data_i, var_double_recording_values[i]->states[data_i],
                     double_to_upper( var_double_recording_values[i]->states[data_i]),
                     double_to_lower( var_double_recording_values[i]->states[data_i]));
                    log_debug("offset of element %d in array is %d",
                        data_i, offsetof(double_timed_state_t, states));
                }
                recording_record_and_notify(
                    i, var_double_recording_values[i],
                    var_recording_size[i], _recording_done_callback);
                log_debug("recording %u bytes", var_recording_size[i]);
            } else if (var_recording_type_index[i] == FLOAT){
                var_float_recording_values[i]->time = time;
                recording_record_and_notify(
                    i, var_float_recording_values[i],
                    var_recording_size[i], _recording_done_callback);
                log_debug("recording %u bytes", var_recording_size[i]);
            } else if (var_recording_type_index[i] == NOT_MATRIX) {
            } else {
                log_error(
                    "WTF! for type index %d", var_recording_type_index[i]);
            }
        } else {
            var_recording_count[i] += var_recording_increment[i];
        }
    }
}

//! \brief does the recording process for spikes and handing over to basic
//! recording.
void neuron_recording_spike_record(uint32_t time, uint8_t spike_channel) {
    // Record any spikes this time step
    if (spike_recording_count == spike_recording_rate) {
        spike_recording_count = 1;
        n_recordings_outstanding += 1;
        if (!out_spikes_record(
                spike_channel, time, n_spike_recording_words,
                _recording_done_callback)) {
            n_recordings_outstanding -= 1;
        }
    } else {
        spike_recording_count += spike_recording_increment;
    }

    // do logging stuff if required
    out_spikes_print();
}

//! \brief sets up state for next recording.
void neuron_recording_setup_for_next_recording(void){
    // Reset the out spikes before starting if a beginning of recording
    if (spike_recording_count == 1) {
        out_spikes_reset();
    }
}

//! \brief resets all states back to start state.
void _reset_record_counter(void) {
    if (spike_recording_rate == 0){
        // Setting increment to zero means spike_index will never equal
        // spike_rate
        spike_recording_increment = 0;
        // Index is not rate so does not record. Nor one so we never reset
        spike_recording_count = 2;
    } else {
        // Increase one each call so count gets to rate
        spike_recording_increment = 1;
        // Using rate here so that the zero time is recorded
        spike_recording_count = spike_recording_rate;
        // Reset as first pass we record no matter what the rate is
        out_spikes_reset();
    }
    for (uint32_t i = 1; i < n_recorded_vars + 1; i++) {
        if (var_recording_rate[i] == 0) {
            // Setting increment to zero means count will never equal rate
            var_recording_increment[i] = 0;
            // Count is not rate so does not record
            var_recording_count[i] = 1;
        } else {
            // Increase one each call so count gets to rate
            var_recording_increment[i] = 1;
            // Using rate here so that the zero time is recorded
            var_recording_count[i] = var_recording_rate[i];
        }
    }
}

//! \brief wrapper to recording finalise
void neuron_recording_finalise(void){
    recording_finalise();
}

//! \brief wrapper to recording do time step update
//! \param[in] time: the time
void neuron_recording_do_timestep_update(uint32_t time){
    recording_do_timestep_update(time);
}

//! \brief reads recording data from sdram
//! \param[in] recording_address: sdram location for the recording data
//! \param[in] n_neurons: the number of neurons to setup for
//! \return bool stating if the read was successful or not
bool _neuron_recording_read_in_elements(address_t address, uint32_t n_neurons) {
     // Load spike recording details
    uint32_t next = basic_recording_words_read;
    log_debug(" basic recording words read = %d", basic_recording_words_read);
    log_debug(" n neurons = %d", n_neurons);
    uint32_t n_words_for_n_neurons = (n_neurons + 3) >> 2;
    log_debug(" n words for n neurons = %d", n_words_for_n_neurons);
    spike_recording_rate = address[next++];
    uint32_t n_neurons_recording_spikes = address[next++];

    // bypass the matrix record point as worthless
    uint32_t spike_type = address[next++];
    var_recording_type_index[0] = spike_type;

    log_debug(
        "spike rate = %d, n neurons reocrding spikes = %d, spike type = %d",
        spike_recording_rate, n_neurons_recording_spikes, spike_type);

    n_spike_recording_words = get_bit_field_size(n_neurons_recording_spikes);
    spin1_memcpy(
        spike_recording_indexes, &address[next], n_neurons * sizeof(uint8_t));
    next += n_words_for_n_neurons;

    // Load other variable recording details
    for (uint32_t i = 1; i < n_recorded_vars + 1; i++) {
        var_recording_rate[i] = address[next++];
        uint32_t n_neurons_recording_var = address[next++];
        var_recording_type_index[i] = address[next++];

        log_debug(
            "matrix %d rate = %d, n neurons reocrding = %d, type = %d",
            i, var_recording_rate[i], n_neurons_recording_var,
            var_recording_type_index[i]);

        if (var_recording_type_index[i] == INT32) {
            var_recording_size[i] =
                (n_neurons_recording_var * sizeof(uint32_t)) +
                TIME_STAMP_SIZE_IN_BYTES;
            log_debug(
                "size of recording for int32 is %d from sizeof %d, n "
                "neurons %d", var_recording_size[i], sizeof(uint32_t),
                n_neurons_recording_var);
        } else if (var_recording_type_index[i] == DOUBLE) {
            log_debug(" recording region %d is a double", i);
            var_recording_size[i] =
                (n_neurons_recording_var * sizeof(double)) +
                (TIME_STAMP_SIZE_IN_BYTES * 2);
            log_debug(
                "size of recording for double is %d from sizeof %d, n "
                "neurons %d", var_recording_size[i], sizeof(double),
                n_neurons_recording_var);
        } else if (var_recording_type_index[i] == FLOAT) {
            log_debug(" recording region %d is a float", i);
            var_recording_size[i] =
                (n_neurons_recording_var * sizeof(float)) +
                TIME_STAMP_SIZE_IN_BYTES;
            log_debug(
                "size of recording for float is %d from sizeof %d, n "
                "neurons %d", var_recording_size[i], sizeof(float),
                n_neurons_recording_var);
        } else {
            log_error(
                "don't recognise this recording type index %d with rate %d "
                " and n neurons %d",
                var_recording_type_index[i],  var_recording_rate[i],
                n_neurons_recording_var);
            return false;
        }

        log_debug(" next is %d", next);
        log_debug(" n neurons = %d", n_neurons);
        log_debug(" var recording index %d is %x", i, var_recording_indexes[i]);
        spin1_memcpy(
            var_recording_indexes[i], &address[next],
            n_neurons * sizeof(uint8_t));

        for (uint32_t index_index = 0; index_index < n_neurons; index_index++){
            uint32_t index_value =
                (uint32_t) var_recording_indexes[i][index_index];
            log_debug(
                "index value for neuron %d is %d", index_index, index_value);
        }
        next += n_words_for_n_neurons;
    }

    _reset_record_counter();
    return true;
}

//! \brief reads recording data from sdram as reset.
//! \param[in] recording_address: sdram location for the recording data
//! \param[in] n_neurons: the number of neurons to setup for
//! \return bool stating if the read was successful or not
bool neuron_recording_reset(address_t address, uint32_t n_neurons){
    recording_reset();
    return _neuron_recording_read_in_elements(address, n_neurons);
}

//! \brief sets up the recording stuff
//! \param[in] recording_address: sdram location for the recording data
//! \param[in] n_neurons: the number of neurons to setup for
//! \return bool stating if the init was successful or not
bool neuron_recording_initialise(
        address_t recording_address, uint32_t *recording_flags,
        uint32_t n_neurons) {
    bool success = recording_initialize(
        recording_address, recording_flags, &basic_recording_words_read);
    if (! success) {
        log_error("failed to init basic recording.");
        return false;
    }
    log_debug("Recording flags = 0x%08x", recording_flags);

    // read in the neuron recording elements
    n_recorded_vars = recording_address[basic_recording_words_read];
    log_debug("n recorded vars = %d", n_recorded_vars);
    basic_recording_words_read += 1;

    // spike recording indexes
    spike_recording_indexes = (uint8_t *) spin1_malloc(
        n_neurons * sizeof(uint8_t));
    if (spike_recording_indexes == NULL) {
        log_error("Could not allocate space for spike_recording_indexes");
        return false;
    }
    var_recording_rate =
        (uint32_t *) spin1_malloc(n_recorded_vars + 1 * sizeof(uint32_t));
    if (var_recording_rate == NULL) {
        log_error("Could not allocate space for var_recording_rate");
        return false;
    }
    var_recording_type_index =
        (uint32_t *) spin1_malloc(n_recorded_vars + 1 * sizeof(uint32_t));
    if (var_recording_type_index == NULL) {
        log_error("Could not allocate space for var_recording_type_index");
        return false;
    }
    var_recording_count =
        (uint32_t *) spin1_malloc(n_recorded_vars + 1 * sizeof(uint32_t));
    if (var_recording_count == NULL) {
        log_error("Could not allocate space for var_recording_count");
        return false;
    }
    var_recording_increment =
        (uint32_t *) spin1_malloc(n_recorded_vars + 1 * sizeof(uint32_t));
    if (var_recording_increment == NULL) {
        log_error("Could not allocate space for var_recording_increment");
        return false;
    }
    var_recording_indexes =
        (uint8_t **) spin1_malloc((n_recorded_vars + 1) * sizeof(uint8_t *));
    log_debug("var index address is %x", var_recording_indexes);
    if (var_recording_indexes == NULL) {
        log_error("Could not allocate space for var_recording_indexes");
        return false;
    }
    var_recording_size =
        (uint32_t *) spin1_malloc(n_recorded_vars + 1 * sizeof(uint32_t));
    if (var_recording_size == NULL) {
        log_error("Could not allocate space for var_recording_size");
        return false;
    }
    for (uint32_t i = 0; i < n_recorded_vars + 1; i++) {
        var_recording_indexes[i] = (uint8_t *) spin1_malloc(
            n_neurons * sizeof(uint8_t));
        log_debug("var index %d address is %x", i, var_recording_indexes[i]);
        if (var_recording_indexes[i] == NULL){
            log_error("failed to allocate memory for recording index %d", i);
            return false;
        }
    }

    // Set up the out spikes array - this is always n_neurons in size to ensure
    // it continues to work if changed between runs, but less might be used in
    // any individual run
    if (!out_spikes_initialize(n_neurons)) {
        return false;
    }

    if (!_neuron_recording_read_in_elements(recording_address, n_neurons)){
        log_error("failed to read in the elements");
        return false;
    }

    var_recording_values =
        (timed_state_t **) spin1_malloc(
            n_recorded_vars + 1 * sizeof(timed_state_t *));
    if (var_recording_values == NULL) {
        log_error("Could not allocate space for var_recording_values");
        return false;
    }
    var_double_recording_values =
        (double_timed_state_t **) spin1_malloc(
            n_recorded_vars * sizeof(double_timed_state_t *));
    if (var_double_recording_values == NULL) {
        log_error("Could not allocate space for var_double_recording_values");
        return false;
    }

    var_float_recording_values =
        (float_timed_state_t **) spin1_malloc(
            n_recorded_vars * sizeof(float_timed_state_t *));
    if (var_float_recording_values == NULL) {
        log_error("Could not allocate space for var_float_recording_values");
        return false;
    }

    for (uint32_t i = 0; i < n_recorded_vars + 1; i++) {
        if (var_recording_type_index[i] == INT32) {
            var_recording_values[i] = (timed_state_t *) spin1_malloc(
                TIME_STAMP_SIZE_IN_BYTES + (sizeof(state_t) * n_neurons));
            if (var_recording_values[i] == NULL) {
                log_error(
                    "Could not allocate space for var_recording_values[%d]", i);
                return false;
            }
        } else if (var_recording_type_index[i] == DOUBLE) {
            var_double_recording_values[i] =
                (double_timed_state_t *) spin1_malloc(
                    TIME_STAMP_SIZE_IN_BYTES +
                    (sizeof(double_timed_state_t) * n_neurons));
            if (var_double_recording_values[i] == NULL) {
                log_error(
                    "Could not allocate space for "
                    "var_double_recording_values[%d]", i);
                return false;
            }
        } else if (var_recording_type_index[i] == FLOAT) {
            var_float_recording_values[i] =
                (float_timed_state_t *) spin1_malloc(
                    TIME_STAMP_SIZE_IN_BYTES +
                    (sizeof(float_timed_state_t) * n_neurons));
            if (var_float_recording_values[i] == NULL) {
                log_error(
                    "Could not allocate space for "
                    "var_float_recording_values[%d]", i);
                return false;
            }
        } else if (var_recording_type_index[i] == NOT_MATRIX) {
            log_debug("don't care, as this is for matrix reading");
        }
        else {
            log_error(
                "don't recognise this recording data type. %d",
                var_recording_type_index[i]);
            return false;
        }
    }

   return true;
}