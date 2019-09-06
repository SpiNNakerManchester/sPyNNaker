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

/*! \file
 *
 *  \brief utility method for decaying a value by a given amount
 *
 *    The API includes:
 *
 *     - decay_s1615 (x, decay)
 *         decays a s1615 value x by a given decay amount
 *     - decay_u1616(x, decay)
 *         decays a u1616 value x by a given decay amount
 *     - decay_s015(x, decay)
 *         decays a s015 value x by a given decay amount
 *     - decay_u016(x, decay)
 *     	   decays a u016 value x by a given decay amount
 *     - decay(x, d)
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

// The following permits us to do a type-generic macro for decay manipulation
/*----------------------------------
 * This method is currently assumed to be faulty. Please do not use it yet.
 * Plan is to fix method and not need to use the private methods directly.
 * issue seems to be in __builtin_types_compatible_p always returning False
 * or at least, that there's the impression that on some types it results in
 * the abort statement and therefore kills scripts dead on SpiNNaker.
 * ---------------------------------
 */
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
