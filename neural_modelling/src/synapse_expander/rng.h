/**
 *! \file
 *! \brief Random number generator interface
 */
#include <common-typedefs.h>

/**
 *! \brief Random number generator "object"
 */
typedef struct rng* rng_t;

/**
 *! \brief Initialise the random number generator
 *! \param[in/out] region The address to read data from - updated to position
 *!                       after data has been read
 *! \return An initialised random number generator that can be used with other
 *!         functions, or NULL if it couldn't be initialised for any reason
 */
rng_t rng_init(address_t *region);

/**
 *! \brief Generate a random number
 *! \param[in] rng The random number generator instance to generate from
 *! \return The number generated between 0 and 0xFFFFFFFF
 */
uint32_t rng_generator(rng_t rng);

/**
 *! \brief Generate an exponentially distributed random number
 *! \param[in] rng The random number generator instance to use
 *! \return The number generated
 */
accum rng_exponential(rng_t rng);

/**
 *! \brief Generate an normally distributed random number
 *! \param[in] rng The random number generator instance to use
 *! \return The number generated
 */
accum rng_normal(rng_t rng);

/**
 *! \brief Finish with a random number generator
 *! \param[in] generator The generator to free
 */
void rng_free(rng_t rng);
