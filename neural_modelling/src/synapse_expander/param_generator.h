/**
 *! \file
 *! \brief Interface for parameter generator
 */
#include <common-typedefs.h>

/**
 *! \brief Parameter generator "object"
 */
typedef struct param_generator* param_generator_t;

/**
 *! \brief Register any parameter generators to be used in the remaining
 *!        functions
 */
void register_param_generators();

/**
 *! \brief Initialise a specific parameter generator
 *! \param[in] hash The identifier of the generator to initialise
 *! \param[in/out] region The address to read data from - updated to position
 *!                       after data has been read
 *! \return An initialised parameter generator that can be used with other
 *!         functions, or NULL if it couldn't be initialised for any reason
 */
param_generator_t param_generator_init(
    uint32_t hash, address_t *region);

/**
 *! \brief Generate values with a parameter generator
 *! \param[in] generator The generator to use to generate values
 *! \param[in] n_indices The number of values to generate
 *! \param[in] pre_neuron_index The index of the neuron in the pre-population
 *!                             being generated
 *! \param[in] indices The n_indices post-neuron indices for each connection
 *! \param[in/out] values An array into which to place the values - will be
 *!                       n_indices in size
 */
void param_generator_generate(
    param_generator_t generator, uint32_t n_indices,
    uint32_t pre_neuron_index, uint16_t *indices, accum *values);

/**
 *! \brief Finish with a parameter generator
 *! \param[in] generator The generator to free
 */
void param_generator_free(param_generator_t generator);
