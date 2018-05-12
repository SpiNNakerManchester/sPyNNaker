#define MAX_DELAY 16

struct delay_value {
    uint32_t delay;
    uint32_t stage;
};

struct delay_value get_delay(uint32_t delay_value, uint32_t max_stage) {
    int32_t delay = delay_value;
    if (delay < 1) {
        log_warning("Delay of %u is too small", delay);
        delay = 1;
    }
    uint32_t stage = (delay - 1) / MAX_DELAY;
    if (stage > max_stage) {
        log_warning("Delay of %u is too big", delay);
        stage = max_stage;
        delay = (stage * MAX_DELAY);
    }
    delay = ((delay - 1) % MAX_DELAY) + 1;
    return (struct delay_value) {.delay = delay, .stage = stage};
}
