// Utility function
static inline int32_t mars_kiss_fixed_point() {

    // **YUCK** copy and pasted rng to allow inlining and also to avoid
    // horrific executable bloat

    /* Seed variables */
    static uint32_t x = 123456789;
    static uint32_t y = 234567891;
    static uint32_t z = 345678912;
    static uint32_t w = 456789123;
    static uint32_t c = 0;
    int32_t t;

    y ^= (y << 5);
    y ^= (y >> 7);
    y ^= (y << 22);
    t = z + w + c;
    z = w;
    c = t < 0;
    w = t & 2147483647;
    x += 1411392427;

    uint32_t random = x + y + w;

    // **YUCK** mask out and return STDP_FIXED_POINT_ONE lowest bits
    return (int32_t)(random & (STDP_FIXED_POINT_ONE - 1));
}
