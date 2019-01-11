#ifndef _THRESHOLD_TYPE_PUSH_BOT_CONTROL_MODULE_H_
#define _THRESHOLD_TYPE_PUSH_BOT_CONTROL_MODULE_H_

#include "threshold_type.h"
#include <spin1_api.h>
#include <stdfix-full-iso.h>

static uint32_t time_between_spikes;
static uint32_t expected_time;

enum send_type {
    SEND_TYPE_INT=0,
    SEND_TYPE_UINT,
    SEND_TYPE_ACCUM,
    SEND_TYPE_UACCUM,
    SEND_TYPE_FRACT,
    SEND_TYPE_UFRACT,
};

typedef struct threshold_type_t {

    // The key to send to update the value
    uint32_t key;

    // True (1) if the value is to be sent as payload, False (0) if just the key
    uint32_t value_as_payload;

    // The minimum allowed value to send as the payload.
    // Values below are clipped to this value
    accum min_value;

    // The maximum allowed value to send as the payload.
    // Values above are clipped to this value
    accum max_value;

    // The time between sending the value
    uint32_t timesteps_between_sending;

    // The time until the next sending of the value (initially 0)
    uint32_t time_until_next_send;

    // Send type
    enum send_type type;

} threshold_type_t;

typedef union int_bits_union {
    int int_value;
    uint uint_value;
} int_bits_union;

static inline uint int_bits(int value) {
    int_bits_union converter;
    converter.int_value = value;
    return converter.uint_value;
}

//! \brief helper method for spreading out the spikes over the timer tick
//! \param[in] key: the key to fire
//! \param[in] payload: the payload to fire
//! \param[in] with_payload: bool saying if a payload is needed or not
static inline void send_packet(
        uint32_t key, uint32_t payload, bool with_payload){

    // Wait until the expected time to send
    while (tc[T1_COUNT] > expected_time) {

        // Do Nothing
    }
    expected_time -= time_between_spikes;

    if (with_payload){
        while (!spin1_send_mc_packet(key, payload, WITH_PAYLOAD)) {
            spin1_delay_us(1);
        }
    }
    else{// Send the spike
        while (!spin1_send_mc_packet(key, 0, NO_PAYLOAD)) {
            spin1_delay_us(1);
        }
    }
}

static inline uint get_payload(enum send_type type, accum value) {
    switch (type) {
    case SEND_TYPE_INT:
        return int_bits((int) value);
    case SEND_TYPE_UINT:
        return (uint) value;
    case SEND_TYPE_ACCUM:
        return int_bits(bitsk(value));
    case SEND_TYPE_UACCUM:
        return bitsuk((unsigned accum) value);
    case SEND_TYPE_FRACT:
        return int_bits(bitslr((long fract) value));
    case SEND_TYPE_UFRACT:
        return bitsulr((long unsigned fract) value);
    default:
        log_error("Unknown enum value %u", value);
        rt_error(RTE_SWERR);
    }
    return 0;
}

static bool threshold_type_is_above_threshold(
        state_t value, threshold_type_pointer_t threshold_type) {

    if (threshold_type->time_until_next_send == 0) {

        if (threshold_type->value_as_payload) {

            accum value_to_send = value;
            if (value > threshold_type->max_value) {
                value_to_send = threshold_type->max_value;
            }
            if (value < threshold_type->min_value) {
                value_to_send = threshold_type->min_value;
            }

            uint payload = get_payload(threshold_type->type, value_to_send);

            log_debug("Sending key=0x%08x payload=0x%08x",
                    threshold_type->key, payload);
            send_packet(threshold_type->key, payload, true);
        } else {
            log_debug("Sending key=0x%08x", threshold_type->key);
            send_packet(threshold_type->key, 0, false);
        }

        threshold_type->time_until_next_send =
                threshold_type->timesteps_between_sending;
    } else {
        --threshold_type->time_until_next_send;
    }
    return false;
}

#endif // _THRESHOLD_TYPE_PUSH_BOT_CONTROL_MODULE_H_
