/*
 * Copyright (c) 2017-2023 The University of Manchester
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

/*! \file
 *
 *  \brief utility method for decaying a value by a given amount
 *
 *    The API includes:
 *
 *     - decay_s1615()
 *         decays a s1615 value x by a given decay amount
 *     - decay_u1616()
 *         decays a u1616 value x by a given decay amount
 *     - decay_s015()
 *         decays a s015 value x by a given decay amount
 *     - decay_u016()
 *     	   decays a u016 value x by a given decay amount
 *     - decay()
 *         is suppose to deduce the x value's type and call one of the above
 *         methods to decay it by a given decay amount.
 */

#ifndef _DECAY_H_
#define _DECAY_H_

#include <common/maths-util.h>
#include <common/neuron-typedefs.h>

//! this is a redefine of the ufract into a decay for easier conversions in
//! the future if the type is redefined
typedef UFRACT decay_t;

//! \brief this method takes a s1615 and decays it by a given amount
//! (denoted by the decay) (to compensate for the valve behaviour of a synapse
//! in biology (spike goes in, synapse opens, then closes slowly)).
//! \param[in] x the s1615 value to decayed
//! \param[in] decay the amount to decay the value by
//! \return the new decayed s1615 value
static inline s1615 decay_s1615(s1615 x, decay_t decay) {
    int64_t s = (int64_t) bitsk(x);
    int64_t u = (int64_t) bitsulr(decay);

    return kbits((int_k_t) ((s * u) >> 32));
}

//! \brief this method takes a s1616 and decays it by a given amount
//! (denoted by the decay) (to compensate for the valve behaviour of a synapse
//! in biology (spike goes in, synapse opens, then closes slowly)).
//! \param[in] x the s1616 value to decayed
//! \param[in] decay the amount to decay the value by
//! \return the new decayed s1616 value
static inline u1616 decay_u1616(u1616 x, decay_t decay) {
    uint64_t s = (uint64_t) bitsuk(x);
    uint64_t u = (uint64_t) bitsulr(decay);

    return ukbits((uint_uk_t) ((s * u) >> 32));
}

//! \brief this method takes a s015 and decays it by a given amount
//! (denoted by the decay) (to compensate for the valve behaviour of a synapse
//! in biology (spike goes in, synapse opens, then closes slowly)).
//! \param[in] x the s015 value to decayed
//! \param[in] decay the amount to decay the value by
//! \return the new decayed s015 value
static inline s015 decay_s015(s015 x, decay_t decay) {
    int64_t s = (int64_t) bitsk(x);
    int64_t u = (int64_t) bitsulr(decay);

    return rbits((int_r_t) ((s * u) >> 32));
}

//! \brief this method takes a s016 and decays it by a given amount
//! (denoted by the decay) (to compensate for the valve behaviour of a synapse
//! in biology (spike goes in, synapse opens, then closes slowly)).
//! \param[in] x the s016 value to decayed
//! \param[in] decay the amount to decay the value by
//! \return the new decayed s016 value
static inline u016 decay_u016(u016 x, decay_t decay) {
    uint64_t s = (uint64_t) bitsuk(x);
    uint64_t u = (uint64_t) bitsulr(decay);

    return urbits((uint_ur_t) ((s * u) >> 32));
}

static inline u032 decay_s1615_to_u032(s1615 x, decay_t decay) {
	uint64_t s = (uint64_t) bitsk(x);
	uint64_t u = (uint64_t) bitsulr(decay);

	return ulrbits((uint_ulr_t) ((s * u) >> 15));
}

// The following permits us to do a type-generic macro for decay manipulation
/*----------------------------------
 * This method is currently assumed to be faulty. Please do not use it yet.
 * Plan is to fix method and not need to use the private methods directly.
 * issue seems to be in __builtin_types_compatible_p always returning False
 * or at least, that there's the impression that on some types it results in
 * the abort statement and therefore kills scripts dead on SpiNNaker.
 * ---------------------------------
 */
//! \brief This is a type-generic decay "function".
//! \param[in] x: the value to decayed
//! \param[in] d: the amount to decay the value by
//! \return the new decayed value
#define decay(x, d) ({ \
    __typeof__(x) tmp = (x); \
    if (__builtin_types_compatible_p(__typeof__(x), s1615)) {\
        tmp = decay_s1615(x, d); \
    } else if (__builtin_types_compatible_p(__typeof__(x), u1616)) {\
        tmp = decay_u1616(x, d); \
    } else if (__builtin_types_compatible_p(__typeof__(x), s015)) {\
        tmp = decay_s015(x, d); \
    } else if (__builtin_types_compatible_p(__typeof__(x), u016)) {\
        tmp = decay_u016(x, d); \
    } else {\
        abort(1); \
    }\
    tmp; \
})

#endif // _DECAY_H_
