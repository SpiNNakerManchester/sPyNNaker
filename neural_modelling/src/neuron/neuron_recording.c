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
#include <bit_field.h>
#include <stddef.h>

// declare spin1_wfi
void spin1_wfi();

//! The number of variables that *can* be recorded - might not be enabled
static uint32_t n_recorded_vars;

//! The number of variables that are of type bitfield.
static uint32_t n_bit_field_based_vars = 0;

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

//! The values of the recorded variables for bitfields
static timed_out_spikes **var_bit_fields_recording_values;

//! The values of the recorded variables for uint32s
static timed_state_t **var_int32_recording_values;

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

// how many bytes are needed for the time stamp (which is a uint32_t)
#define TIME_STAMP_SIZE_IN_BYTES sizeof(uint32_t)

// the different types of data that can be recorded
typedef enum recording_type_enum {
    BIT_FIELD = 0,
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

//! \brief returns the number of variables that are of type bitfield.
//! \return the number of bitfield vars
uint32_t neuron_recording_get_n_bit_field_vars(void) {
    return n_bit_field_based_vars;
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
void neuron_recording_set_int32_recorded_param(
        uint32_t recording_var_index, uint32_t neuron_index, state_t value) {
    uint32_t index = var_recording_indexes[recording_var_index][neuron_index];
    var_int32_recording_values[recording_var_index]->states[index] = value;
}


//! \brief stores a double recording of a matrix based variable
//! \param[in] recording_var_index: which recording variable to write this is
//! \param[in] neuron_index: which neuron to set the spike for
//! \param[in] value: the data to store
void neuron_recording_set_double_recorded_param(
        uint32_t recording_var_index, uint32_t neuron_index, double value){
    uint8_t index = var_recording_indexes[recording_var_index][neuron_index];
    var_double_recording_values[recording_var_index]->states[index] = value;
}

//! \brief stores a double recording of a matrix based variable
//! \param[in] recording_var_index: which recording variable to write this is
//! \param[in] neuron_index: which neuron to set the spike for
//! \param[in] value: the data to store
void neuron_recording_set_float_recorded_param(
        uint32_t recording_var_index, uint32_t neuron_index, float value){
    uint32_t index = var_recording_indexes[recording_var_index][neuron_index];
    var_float_recording_values[recording_var_index]->states[index] = value;
}

//! \brief stores a recording of a bitfield based variable
void neuron_recording_set_spike(
        uint32_t recording_var_index, uint32_t neuron_index){
    // Record the spike
    uint32_t index = var_recording_indexes[recording_var_index][neuron_index];
    bit_field_set(
        &var_bit_fields_recording_values[recording_var_index]->out_spikes[0],
        index);
    if (index != 6){
        log_info("setting spike for neuron %d goes to %d", neuron_index, index);
    }
}

//! \brief does the recording process of handing over to basic recording
//! \param[in] time: the time to put into the recording stamps.
void neuron_recording_record(uint32_t time) {
    // go through all recordings

    for (uint32_t i = 0; i < n_recorded_vars; i++) {
        // if the rate says record

        if (var_recording_count[i] == var_recording_rate[i]) {
            var_recording_count[i] = 1;
            n_recordings_outstanding += 1;

            switch (var_recording_type_index[i]) {
                case INT32:  // set the time and dump to recording
                    var_int32_recording_values[i]->time = time;
                    recording_record_and_notify(
                        i, var_int32_recording_values[i], var_recording_size[i],
                        _recording_done_callback);
                    break;
                case DOUBLE:  // set the time and dump to recording
                    var_double_recording_values[i]->time = time;
                    recording_record_and_notify(
                        i, var_double_recording_values[i],
                        var_recording_size[i], _recording_done_callback);
                    break;
                case FLOAT:  // set the time and dump to recording
                    var_float_recording_values[i]->time = time;
                    recording_record_and_notify(
                        i, var_float_recording_values[i],
                        var_recording_size[i], _recording_done_callback);
                    break;
                case BIT_FIELD:  // only record if there is stuff to record
                    if (empty_bit_field(
                            &var_bit_fields_recording_values[i]->out_spikes[0],
                            var_recording_size[i] - TIME_STAMP_SIZE_IN_BYTES)) {
                        n_recordings_outstanding -= 1;
                    } else {  // set the time and dump to recording
                        var_bit_fields_recording_values[i]->time = time;
                        recording_record_and_notify(
                            i, var_bit_fields_recording_values[i],
                            var_recording_size[i], _recording_done_callback);
                    }
                    break;
                default:
                    log_error(
                        "WTF! for type index %d", var_recording_type_index[i]);
            }
        } else {
            var_recording_count[i] += var_recording_increment[i];
        }
    }
}

//! \brief sets up state for next recording.
void neuron_recording_setup_for_next_recording(void){
    // Reset the bitfields before starting if a beginning of recording. But only
    // if the bitfields are recording anything in the first place.
    for (uint32_t i = 0; i < n_recorded_vars; i++) {
        if (var_recording_type_index[i] == BIT_FIELD &&
                var_recording_rate[i] != 0 && var_recording_count[i] == 1) {
            clear_bit_field(
                &var_bit_fields_recording_values[i]->out_spikes[0],
                var_recording_size[i] - TIME_STAMP_SIZE_IN_BYTES);
        }
    }
}

//! \brief resets all states back to start state.
void _reset_record_counter(void) {
    for (uint32_t i = 0; i < n_recorded_vars; i++) {
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

            // clear the bitfield if its a bitfield region
            if (var_recording_type_index[i] == BIT_FIELD) {
                // Reset as first pass we record no matter what the rate is
                clear_bit_field(
                    &var_bit_fields_recording_values[i]->out_spikes[0],
                    var_recording_size[i] - TIME_STAMP_SIZE_IN_BYTES);
            }
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
bool _neuron_recording_read_in_elements(
        address_t address, uint32_t n_neurons) {

    // determine how many words for the n neurons
    uint32_t n_words_for_n_neurons = (n_neurons + 3) >> 2;

    // reset counter for safety when rereading the system
    n_bit_field_based_vars = 0;

    // Load other variable recording details
    uint32_t next = basic_recording_words_read;
    for (uint32_t i = 0; i < n_recorded_vars; i++) {
        var_recording_rate[i] = address[next++];
        uint32_t n_neurons_recording_var = address[next++];
        var_recording_type_index[i] = address[next++];

        switch (var_recording_type_index[i]) {
            case INT32:
                var_recording_size[i] =
                    (n_neurons_recording_var * sizeof(uint32_t)) +
                    TIME_STAMP_SIZE_IN_BYTES;
                break;
            case DOUBLE:
                var_recording_size[i] =
                    (n_neurons_recording_var * sizeof(double)) +
                    (TIME_STAMP_SIZE_IN_BYTES * 2);
                break;
            case FLOAT:
                var_recording_size[i] =
                    (n_neurons_recording_var * sizeof(float)) +
                    TIME_STAMP_SIZE_IN_BYTES;
                break;
            case BIT_FIELD:
                var_recording_size[i] =
                    (get_bit_field_size(n_neurons_recording_var) *
                    sizeof(uint32_t)) + TIME_STAMP_SIZE_IN_BYTES;
                n_bit_field_based_vars += 1;
                break;
            default:
                log_error(
                    "don't recognise this recording type index %d with rate
                    " %d and n neurons %d",
                    var_recording_type_index[i],  var_recording_rate[i],
                    n_neurons_recording_var);
                return false;
                break;
        }
        // copy over the indexes
        spin1_memcpy(
            var_recording_indexes[i], &address[next],
            n_neurons * sizeof(uint8_t));

        // move to next region data point
        next += n_words_for_n_neurons;
    }
    return true;
}

//! \brief reads recording data from sdram as reset.
//! \param[in] recording_address: sdram location for the recording data
//! \param[in] n_neurons: the number of neurons to setup for
//! \return bool stating if the read was successful or not
bool neuron_recording_reset(address_t address, uint32_t n_neurons){
    recording_reset();
    bool success = _neuron_recording_read_in_elements(address, n_neurons);
    if (!success){
        log_error("failed to reread in the new elements after reset");
        return false;
    }
    return true;
}

//! \brief handles all the dtcm allocations
//! \param[in] n_recorded_vars: how many regions are to be recordings
//! \param[in] n_neurons: how many neurons to set dtcm for
static inline bool _allocate_dtcm(
        uint32_t n_recorded_vars, uint32_t n_neurons) {

    // allocate dtcm for the rates
    var_recording_rate =
        (uint32_t *) spin1_malloc(n_recorded_vars * sizeof(uint32_t));
    if (var_recording_rate == NULL) {
        log_error("Could not allocate space for var_recording_rate");
        return false;
    }

    // allocate dtcm for the recording types
    var_recording_type_index =
        (uint32_t *) spin1_malloc(n_recorded_vars * sizeof(uint32_t));
    if (var_recording_type_index == NULL) {
        log_error("Could not allocate space for var_recording_type_index");
        return false;
    }

    // allocate dtcm for the counts
    var_recording_count =
        (uint32_t *) spin1_malloc(n_recorded_vars * sizeof(uint32_t));
    if (var_recording_count == NULL) {
        log_error("Could not allocate space for var_recording_count");
        return false;
    }

    // allocate dtcm for the increments
    var_recording_increment =
        (uint32_t *) spin1_malloc(n_recorded_vars * sizeof(uint32_t));
    if (var_recording_increment == NULL) {
        log_error("Could not allocate space for var_recording_increment");
        return false;
    }

    // allocate dtcm for the overall holder for indexes
    var_recording_indexes =
        (uint8_t **) spin1_malloc(n_recorded_vars * sizeof(uint8_t *));
    if (var_recording_indexes == NULL) {
        log_error("Could not allocate space for var_recording_indexes");
        return false;
    }

    // allocate dtcm for sizes
    var_recording_size =
        (uint32_t *) spin1_malloc(n_recorded_vars * sizeof(uint32_t));
    if (var_recording_size == NULL) {
        log_error("Could not allocate space for var_recording_size");
        return false;
    }

    // allocate dtcm for indexes for each recording region
    for (uint32_t i = 0; i < n_recorded_vars; i++) {
        var_recording_indexes[i] = (uint8_t *) spin1_malloc(
            n_neurons * sizeof(uint8_t));
        if (var_recording_indexes[i] == NULL){
            log_error("failed to allocate memory for recording index %d", i);
            return false;
        }
    }

    // allocate dtcm for bitfields
    var_bit_fields_recording_values = (timed_out_spikes **) spin1_malloc(
        n_recorded_vars * sizeof(timed_out_spikes *));
    if (var_bit_fields_recording_values == NULL) {
        log_error(
            "Count not allocate space for var_bit_fields_recording_values");
        return false;
    }

    // allocate dtcm for uint32t pointers
    var_int32_recording_values = (timed_state_t **) spin1_malloc(
        n_recorded_vars * sizeof(timed_state_t *));
    if (var_int32_recording_values == NULL) {
        log_error("Could not allocate space for var_int32_recording_values");
        return false;
    }

    // allocate dtcm for double pointers
    var_double_recording_values =
        (double_timed_state_t **) spin1_malloc(
            n_recorded_vars * sizeof(double_timed_state_t *));
    if (var_double_recording_values == NULL) {
        log_error("Could not allocate space for var_double_recording_values");
        return false;
    }

    // allocate for float pointers
    var_float_recording_values =
        (float_timed_state_t **) spin1_malloc(
            n_recorded_vars * sizeof(float_timed_state_t *));
    if (var_float_recording_values == NULL) {
        log_error("Could not allocate space for var_float_recording_values");
        return false;
    }

    // successfully allocated all dtcm.
    return true;
}

//! \brief sets up the recording stuff
//! \param[in] recording_address: sdram location for the recording data
//! \param[in] n_neurons: the number of neurons to setup for
//! \param[out] recording_flags: the flags set by the basic recording
//! \return bool stating if the init was successful or not
bool neuron_recording_initialise(
        address_t recording_address, uint32_t *recording_flags,
        uint32_t n_neurons) {

    // boot up the basic recording
    bool success = recording_initialize(
        recording_address, recording_flags, &basic_recording_words_read);
    if (! success) {
        log_error("failed to init basic recording.");
        return false;
    }

    // read in the n neuron recording elements
    n_recorded_vars = recording_address[basic_recording_words_read];
    basic_recording_words_read += 1;

    bool dtcm_allocated = _allocate_dtcm(n_recorded_vars, n_neurons);
    if (!dtcm_allocated){
        log_error("failed to allocate dtcm for the neuron recording structs.");
    }

    // read in the sdram params into the malloced data objects
    if (!_neuron_recording_read_in_elements(recording_address, n_neurons)){
        log_error("failed to read in the elements");
        return false;
    }

    // malloc values based off the type index's read from sdram.
    for (uint32_t i = 0; i < n_recorded_vars; i++) {
        switch (var_recording_type_index[i]) {
            case INT32:
                var_int32_recording_values[i] = (timed_state_t *) spin1_malloc(
                    TIME_STAMP_SIZE_IN_BYTES + (sizeof(state_t) * n_neurons));
                if (var_int32_recording_values[i] == NULL) {
                    log_error(
                        "Could not allocate space for "
                        "var_int32_recording_values[%d]", i);
                    return false;
                }
                break;
            case DOUBLE:
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
                break;
            case FLOAT:
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
                break;
            case BIT_FIELD:
                // determine size of bitfield
                var_bit_fields_recording_values[i] = spin1_malloc(
                    sizeof(timed_out_spikes) + (
                        (var_recording_size[i] - TIME_STAMP_SIZE_IN_BYTES) *
                        sizeof(uint32_t)));
                if (var_bit_fields_recording_values[i] == NULL){
                    log_error(
                        "Could not allocate space for "
                        "var_bit_fields_recording_values[%d]", i);
                    return false;
                }

                // set all the bits to false
                clear_bit_field(
                    &var_bit_fields_recording_values[i]->out_spikes[0],
                    var_recording_size[i] - TIME_STAMP_SIZE_IN_BYTES);
                break;
            default:
                log_error(
                    "don't recognise this recording data type. %d",
                    var_recording_type_index[i]);
                return false;
       }
   }

   // reset stuff
   _reset_record_counter();

   return true;
}