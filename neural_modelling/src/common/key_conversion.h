#ifndef _KEY_CONVERSION_H_
#define _KEY_CONVERSION_H_

#include "neuron-typedefs.h"

static inline key_t key_x(key_t k) {
    return (k >> 24);
}

static inline key_t key_y(key_t k) {
    return ((k >> 16) & 0xFF);
}

static inline key_t key_p(key_t k) {
    return ((k >> 11) & 0x1F);
}

static inline key_t make_key(key_t x, key_t y, key_t p) {
    return ((x << 24) | (y << 16) | ((p - 1) << 11));
}

static inline uint32_t make_pid(key_t x, key_t y, key_t p) {
    return (((x << 3) + y) * 18 + p);
}

#endif // _KEY_CONVERSION_H_
