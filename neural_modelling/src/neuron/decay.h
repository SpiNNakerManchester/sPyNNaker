#ifndef _DECAY_H_
#define _DECAY_H_

#include "../common/maths-util.h"
#include "../common/neuron-typedefs.h"

typedef UFRACT decay_t;

static inline s1615 decay_s1615(s1615 x, decay_t decay) {
    int64_t s = (int64_t) (bitsk(x));
    int64_t u = (int64_t) (bitsulr(decay));

    return (kbits((int_k_t) ((s * u) >> 32)));
}

static inline u1616 decay_u1616(u1616 x, decay_t decay) {
    uint64_t s = (uint64_t) (bitsuk(x));
    uint64_t u = (uint64_t) (bitsulr(decay));

    return (ukbits((uint_uk_t) ((s * u) >> 32)));
}

static inline s015 decay_s015(s015 x, decay_t decay) {
    int64_t s = (int64_t) (bitsk(x));
    int64_t u = (int64_t) (bitsulr(decay));

    return (rbits((int_r_t) ((s * u) >> 32)));
}

static inline u016 decay_u016(u016 x, decay_t decay) {
    uint64_t s = (uint64_t) (bitsuk(x));
    uint64_t u = (uint64_t) (bitsulr(decay));

    return (urbits((uint_ur_t) ((s * u) >> 32)));
}

// The following permits us to do a type-generic macro for decay manipulation
#define decay(x,d) \
  ({ \
    __typeof__ (x) tmp = (x); \
    if      (__builtin_types_compatible_p (__typeof__(x), s1615)) \
      tmp = decay_s1615 (x,d); \
    else if (__builtin_types_compatible_p (__typeof__(x), u1616)) \
      tmp = decay_u1616 (x,d); \
    else if (__builtin_types_compatible_p (__typeof__(x), s015)) \
      tmp = decay_s015 (x,d); \
    else if (__builtin_types_compatible_p (__typeof__(x), u016)) \
      tmp = decay_u016 (x,d); \
    else \
      abort (1); \
    tmp; \
})

#endif // _DECAY_H_
