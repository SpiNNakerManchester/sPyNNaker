/**
 *! \file
 * \brief The implementation of the functions in connection_generator.h
 */

#include "connection_generator.h"
#include <spin1_api.h>
#include <debug.h>

#include "connection_generators/connection_generator_one_to_one.h"
#include "connection_generators/connection_generator_all_to_all.h"
#include "connection_generators/connection_generator_fixed_prob.h"
#include "connection_generators/connection_generator_fixed_total.h"

/**
 *! \brief The number of known generators
 */
#define N_CONNECTION_GENERATORS 4

/**
 *! \brief The data for a connection generator
 */
struct connection_generator {
    uint32_t index;
    void *data;
};

/**
 *! \brief A "class" for connection generators
 */
struct connection_generator_info {

    /**
     *! \brief The hash of the generator
     */
    uint32_t hash;

    /**
     *! \brief Initialise the generator
     *! \param[in/out] region Region to read parameters from.  Should be updated
     *!                       to position just after parameters after calling.
     *! \return An data to be passed in to other functions later on
     */
    void* (*initialize)(address_t *region);

    /**
     *! \brief Generate connections
     *! \param[in] data The data for the connection generator, returned by the
     *!                 initialise function
     *! \param[in] pre_slice_start The start of the slice of the pre-population
     *!                            being generated
     *! \param[in] pre_slice_count The number of neurons in the slice of the
     *!                            pre-population being generated
     *! \param[in] pre_neuron_index The index of the neuron in the
     *!                             pre-population being generated
     *! \param[in] post_slice_start The start of the slice of the
     *!                             post-population being generated
     *! \param[in] post_slice_count The number of neurons in the slice of the
     *!                             post-population being generated
     *! \param[in] max_row_length The maximum number of connections to generate
     *! \param[in/out] indices An array into which the core-relative
     *!                        post-indices should be placed.  This will be
     *!                        initialised to be max_row_length in size
     *! \return The number of connections generated
     */
    uint32_t (*generate)(
        void *data, uint32_t pre_slice_start, uint32_t pre_slice_count,
        uint32_t pre_neuron_index, uint32_t post_slice_start,
        uint32_t post_slice_count, uint32_t max_row_length, uint16_t *indices);

    /**
     *! \brief Free any data for the connector
     *! \param[in] data The data to free
     */
    void (*free)(void *data);
};

//! \brief An Array of known generators
struct connection_generator_info connection_generators[N_CONNECTION_GENERATORS];

void register_connection_generators() {
    // Register each of the known connection generators
    // For now, hash is just an index agreed between Python and here

    // One To One Connector
    connection_generators[0].hash = 0;
    connection_generators[0].initialize =
        connection_generator_one_to_one_initialise;
    connection_generators[0].generate =
        connection_generator_one_to_one_generate;
    connection_generators[0].free =
        connection_generator_one_to_one_free;

    // All To All Connector
    connection_generators[1].hash = 1;
    connection_generators[1].initialize =
        connection_generator_all_to_all_initialise;
    connection_generators[1].generate =
        connection_generator_all_to_all_generate;
    connection_generators[1].free =
        connection_generator_all_to_all_free;

    // Fixed-Probability Connector
    connection_generators[2].hash = 2;
    connection_generators[2].initialize =
        connection_generator_fixed_prob_initialise;
    connection_generators[2].generate =
        connection_generator_fixed_prob_generate;
    connection_generators[2].free =
        connection_generator_fixed_prob_free;

    // Fixed Total Number (Multapse) Connector
    connection_generators[3].hash = 3;
    connection_generators[3].initialize =
        connection_generator_fixed_total_initialise;
    connection_generators[3].generate =
        connection_generator_fixed_total_generate;
    connection_generators[3].free =
        connection_generator_fixed_total_free;
}

connection_generator_t connection_generator_init(
        uint32_t hash, address_t *in_region) {

    // Look through the known generators
    for (uint32_t i = 0; i < N_CONNECTION_GENERATORS; i++) {

        // If the hash requested matches the hash of the generator, use it
        if (hash == connection_generators[i].hash) {

            // Prepare a space for the data
            address_t region = *in_region;
            struct connection_generator *generator = spin1_malloc(
                sizeof(struct connection_generator));
            if (generator == NULL) {
                log_error("Could not create generator");
                return NULL;
            }

            // Store the index
            generator->index = i;

            // Initialise the generator and store the data
            generator->data = connection_generators[i].initialize(&region);
            *in_region = region;
            return generator;
        }
    }
    log_error("Connection generator with hash %u not found", hash);
    return NULL;
}

uint32_t connection_generator_generate(
        connection_generator_t generator, uint32_t pre_slice_start,
        uint32_t pre_slice_count, uint32_t pre_neuron_index,
        uint32_t post_slice_start, uint32_t post_slice_count,
        uint32_t max_row_length, uint16_t *indices) {
    return connection_generators[generator->index].generate(
        generator->data, pre_slice_start, pre_slice_count,
        pre_neuron_index, post_slice_start, post_slice_count,
        max_row_length, indices);
}

void connection_generator_free(connection_generator_t generator) {
    connection_generators[generator->index].free(generator->data);
    sark_free(generator);
}
