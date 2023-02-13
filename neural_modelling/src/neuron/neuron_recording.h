/*
 * Copyright (c) 2019-2023 The University of Manchester
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

//! \file
//! \brief Recording of the state of a neuron (spiking, voltage, etc.)

#ifndef _NEURON_RECORDING_H_
#define _NEURON_RECORDING_H_

#include <common/neuron-typedefs.h>
#include <bit_field.h>
#include <recording.h>
#include <wfi.h>
#include <stddef.h>

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
static uint16_t **neuron_recording_indexes;

//! The index to record each bitfield variable to for each neuron
static uint16_t **bitfield_recording_indexes;

//! An array of recording information structures
static recording_info_t *recording_info;

//! An array of bitfield information structures
static bitfield_info_t *bitfield_info;

//! An array of spaces into which recording values can be written
static uint8_t **recording_values;

//! An array of spaces into which bitfields can be written
static uint32_t **bitfield_values;

//! The number of recordings outstanding
static volatile uint32_t n_recordings_outstanding = 0;

//! The address of the recording region to read on reset
static void *reset_address;

//! When bitwise anded with a number will floor to the nearest multiple of 2
#define FLOOR_TO_2 0xFFFFFFFE

//! Add to a number before applying floor to 2 to turn it into a ceil operation
#define CEIL_TO_2 1

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
    uint16_t index = neuron_recording_indexes[var_index][neuron_index];
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
    uint16_t index = neuron_recording_indexes[var_index][neuron_index];
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
    uint16_t index = neuron_recording_indexes[var_index][neuron_index];
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
    uint16_t index = neuron_recording_indexes[var_index][neuron_index];
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
    uint32_t index = bitfield_recording_indexes[var_index][neuron_index];
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

//! \brief resets all states back to start state.
static void reset_record_counter(void) {
    for (uint32_t i = 0; i < N_RECORDED_VARS; i++) {
        if (recording_info[i].rate == 0) {
            // Setting increment to zero means count will never equal rate
            recording_info[i].increment = 0;

            // Count is not rate so does not record, but not 1 so it does not reset!
            recording_info[i].count = 2;
        } else {
            // Increase one each call so count gets to rate
            recording_info[i].increment = 1;

            // Using rate here so that the zero time is recorded
            recording_info[i].count = recording_info[i].rate;
        }
    }

    // clear the bitfields
    for (uint32_t i = 0; i < N_BITFIELD_VARS; i++) {
        if (bitfield_info[i].rate == 0) {
            // Setting increment to zero means count will never equal rate
            bitfield_info[i].increment = 0;

            // Count is not rate so does not record, but not 1 so it does not reset!
            bitfield_info[i].count = 2;
        } else {
            // Increase one each call so count gets to rate
            bitfield_info[i].increment = 1;

            // Using rate here so that the zero time is recorded
            bitfield_info[i].count = bitfield_info[i].rate;
            clear_bit_field(bitfield_info[i].values->bits,
                    bitfield_info[i].n_words);
        }
    }
}

//! \brief the number of bytes used in bitfield recording for n_neurons
//! \param[in] n_neurons: The number of neurons to create a bitfield for
//! \return the size of the bitfield data structure for the number of neurons
static inline uint32_t bitfield_data_size(uint32_t n_neurons) {
    return sizeof(bitfield_values_t) + (get_bit_field_size(n_neurons) * sizeof(uint32_t));
}

//! \brief reads recording data from SDRAM
//! \param[in] recording_address: SDRAM location for the recording data
//! \param[in] n_neurons: the number of neurons to setup for
//! \return Whether the read was successful
static bool neuron_recording_read_in_elements(
        void *recording_address, uint32_t n_neurons) {
    // Round up the number of bytes to align at a word boundary i.e. round to
    // the next multiple of 2
    uint32_t ceil_n_entries = (n_neurons + CEIL_TO_2) & FLOOR_TO_2;


    // GCC lets you define a struct like this!
    typedef struct neuron_recording_data {
        uint32_t rate;
        uint32_t n_neurons_recording;
        uint32_t element_size;
        uint16_t indices[ceil_n_entries];
    } neuron_recording_data_t;

    neuron_recording_data_t *data = recording_address;

    for (uint32_t i = 0; i < N_RECORDED_VARS; i++) {
        recording_info[i].rate = data[i].rate;
        uint32_t n_neurons_rec = data[i].n_neurons_recording;
        recording_info[i].element_size = data[i].element_size;
        recording_info[i].size = sizeof(recording_values_t)
                + (n_neurons_rec * recording_info[i].element_size);
        // There is an extra "neuron" in the data used when one of the neurons
        // is *not* recording, to avoid a check
        uint32_t alloc_size = recording_info[i].size +
                recording_info[i].element_size;

        // allocate memory for the recording
        if (recording_info[i].values == NULL) {
            recording_info[i].values = spin1_malloc(alloc_size);
            if (recording_info[i].values == NULL) {
                log_error("couldn't allocate recording data space %u for %d",
                        alloc_size, i);
                return false;
            }
            recording_values[i] = recording_info[i].values->data;
        }

        // copy over the indexes
        spin1_memcpy(neuron_recording_indexes[i], data[i].indices,
            n_neurons * sizeof(uint16_t));
    }

    typedef struct bitfield_recording_data {
        uint32_t rate;
        uint32_t n_neurons_recording;
        uint16_t indices[ceil_n_entries];
    } bitfield_recording_data_t;

    bitfield_recording_data_t *bitfield_data =
            (bitfield_recording_data_t *) &data[N_RECORDED_VARS];

    for (uint32_t i = 0; i < N_BITFIELD_VARS; i++) {
        bitfield_info[i].rate = bitfield_data[i].rate;
        uint32_t n_neurons_rec = bitfield_data[i].n_neurons_recording;
        bitfield_info[i].size = bitfield_data_size(n_neurons_rec);
        // There is an extra "neuron" in the data used when one of the neurons
        // is *not* recording, to avoid a check
        uint32_t alloc_size = bitfield_data_size(n_neurons_rec + 1);

        // allocate memory for the recording
        if (bitfield_info[i].values == NULL) {
            bitfield_info[i].values = spin1_malloc(alloc_size);
            if (bitfield_info[i].values == NULL) {
                log_error("couldn't allocate bitfield recording data space for %d", i);
                return false;
            }
            // There is an extra "neuron" in the data used when one of the
            // neurons is *not* recording, to avoid a check
            bitfield_info[i].n_words = get_bit_field_size(n_neurons_rec + 1);
            bitfield_values[i] = bitfield_info[i].values->bits;
        }

        // copy over the indexes
        spin1_memcpy(bitfield_recording_indexes[i], bitfield_data[i].indices,
            n_neurons * sizeof(uint16_t));
    }
    return true;
}

//! \brief reads recording data from sdram on reset.
//! \param[in] n_neurons: the number of neurons to setup for
//! \return bool stating if the read was successful or not
bool neuron_recording_reset(uint32_t n_neurons) {
    if (!neuron_recording_read_in_elements(reset_address, n_neurons)) {
        log_error("failed to reread in the new elements after reset");
        return false;
    }
    return true;
}

//! \brief handles all the DTCM allocations for recording words
//! \param[in] n_neurons: how many neurons to set DTCM for
//! \return True on success
static inline bool allocate_word_dtcm(uint32_t n_neurons) {
    recording_info = spin1_malloc(N_RECORDED_VARS * sizeof(recording_info_t));
    if (recording_info == NULL) {
        log_error("Could not allocated space for recording_info");
        return false;
    }

    // allocate dtcm for the overall holder for indexes
    neuron_recording_indexes =
            spin1_malloc(N_RECORDED_VARS * sizeof(uint16_t *));
    if (neuron_recording_indexes == NULL) {
        log_error("Could not allocate space for var_recording_indexes");
        return false;
    }

    recording_values = spin1_malloc(N_RECORDED_VARS * sizeof(uint8_t *));
    if (recording_values == NULL) {
        log_error("Could not allocate space for recording_values");
        return false;
    }

    for (uint32_t i = 0; i < N_RECORDED_VARS; i++) {
        // clear recorded values pointer
        recording_info[i].values = NULL;

        // allocate dtcm for indexes for each recording region
        neuron_recording_indexes[i] = spin1_malloc(n_neurons * sizeof(uint16_t));
        if (neuron_recording_indexes[i] == NULL) {
            log_error("failed to allocate memory for recording index %d", i);
            return false;
        }
    }

    // successfully allocated all DTCM.
    return true;
}

//! \brief handles all the DTCM allocations for recording bitfields
//! \param[in] n_neurons: how many neurons to set DTCM for
//! \return True on success
static inline bool allocate_bitfield_dtcm(uint32_t n_neurons) {
    bitfield_info = spin1_malloc(N_BITFIELD_VARS * sizeof(bitfield_info_t));
    if (bitfield_info == NULL) {
        log_error("Failed to allocate space for bitfield_info");
        return false;
    }

    // allocate dtcm for the overall holder for indexes
    bitfield_recording_indexes =
            spin1_malloc(N_BITFIELD_VARS * sizeof(uint16_t *));
    if (bitfield_recording_indexes == NULL) {
        log_error("Could not allocate space for bitfield_recording_indexes");
        return false;
    }

    bitfield_values = spin1_malloc(N_BITFIELD_VARS * sizeof(uint32_t *));
    if (bitfield_values == NULL) {
        log_error("Could not allocate space for bitfield_values");
        return false;
    }

    for (uint32_t i = 0; i < N_BITFIELD_VARS; i++) {
        // clear recorded values pointer
        bitfield_info[i].values = NULL;

        // allocate dtcm for indexes for each recording region
        bitfield_recording_indexes[i] =
                spin1_malloc(n_neurons * sizeof(uint16_t));
        if (bitfield_recording_indexes[i] == NULL) {
            log_error("failed to allocate memory for bitfield index %d", i);
            return false;
        }
    }

    // successfully allocated all DTCM.
    return true;
}

//! The heading of the neuron recording region.
typedef struct neuron_recording_header {
    //! The number of word-sized variables to record
    uint32_t n_recorded_vars;
    //! The number of bitfield variables to record
    uint32_t n_bitfield_vars;
} neuron_recording_header_t;

//! \brief sets up the recording stuff
//! \param[in] recording_address: sdram location for the recording data
//! \param[in] n_neurons: the number of neurons to setup for
//! \param[out] n_rec_regions_used: Output the number of regions used by neuron
//!            recording
//! \return bool stating if the init was successful or not
bool neuron_recording_initialise(
        void *recording_address, uint32_t n_neurons,
        uint32_t *n_rec_regions_used) {
    // boot up the basic recording
    void *data_addr = recording_address;

    // Verify the number of recording and bitfield elements
    neuron_recording_header_t *header = data_addr;
    if (header->n_recorded_vars != N_RECORDED_VARS) {
        log_error("Data spec number of recording variables %d != "
                "neuron implementation number of recorded variables %d",
                header->n_recorded_vars, N_RECORDED_VARS);
        return false;
    }
    if (header->n_bitfield_vars != N_BITFIELD_VARS) {
        log_error("Data spec number of bitfield variables %d != "
                "neuron implementation number of bitfield variables %d",
                header->n_bitfield_vars, N_BITFIELD_VARS);
        return false;
    }
    // Copy the number of regions used
    *n_rec_regions_used = header->n_recorded_vars + header->n_bitfield_vars;
    data_addr = &header[1];

    if (!allocate_word_dtcm(n_neurons)) {
        log_error("failed to allocate DTCM for the neuron recording structs.");
        return false;
    }
    if (!allocate_bitfield_dtcm(n_neurons)) {
        log_error("failed to allocate DTCM for the bitfield recording structs");
        return false;
    }

    // read in the sdram params into the allocated data objects
    reset_address = data_addr;
    if (!neuron_recording_read_in_elements(data_addr, n_neurons)) {
        log_error("failed to read in the elements");
        return false;
    }

    // reset stuff
    reset_record_counter();

    return true;
}

#endif //_NEURON_RECORDING_H_
