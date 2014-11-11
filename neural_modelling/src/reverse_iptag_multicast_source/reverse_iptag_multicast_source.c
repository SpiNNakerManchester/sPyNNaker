#include "../common/neuron-typedefs.h"

#include <data_specification.h>
#include <debug.h>
#include <simulation.h>
#include <string.h>

#define APPLICATION_MAGIC_NUMBER 0xAC9

// Globals
static uint32_t time;
static bool apply_prefix;
static bool check;
static uint32_t prefix;
static uint32_t key_space;
static uint32_t mask;
static uint32_t incorrect_keys;
static uint32_t key_left_shift;
static uint32_t simulation_ticks;

typedef struct {
    uint16_t event;
    uint16_t payload;
} event16_t;

// Callbacks
void timer_callback(uint unused0, uint unused1) {
    use(unused0);
    use(unused1);
    time++;

    if ((simulation_ticks != UINT32_MAX) && (time >= simulation_ticks)) {
        log_info("Simulation complete.");
        log_info("Incorrect keys discarded: %d", incorrect_keys);
        spin1_exit(0);
    }
}

void process_16_bit_packets(
        void* event_pointer, bool pkt_format, uint32_t length,
        uint32_t pkt_prefix, uint32_t pkt_payload_prefix, bool payload,
        bool pkt_payload_prefix_apply) {
    uint32_t i;

    log_debug("process_16_bit_packets");
    log_debug("event_pointer: %08x", (uint32_t) event_pointer);
    log_debug("length: %d", length);
    log_debug("pkt_prefix: %08x", pkt_prefix);
    log_debug("pkt_payload_prefix: %08x", pkt_payload_prefix);
    log_debug("payload on: %d", payload);
    log_debug("pkt_format: %d", pkt_format);

    if (!payload && !pkt_payload_prefix_apply) {
        log_debug("16 bit, no payload");

        uint16_t *events_array = (uint16_t *) event_pointer;

        for (i = 0; i < length; i++) {
            uint32_t key = (uint32_t) (events_array[i]);

            if (!pkt_format) {
                key <<= 16;
            }
            key |= pkt_prefix;

            log_debug("mc packet 16 key: %08x", key);
            log_debug("check before send packet: %d",
                    (!check) || (check && ((key & mask) == key_space)));

            if ((!check) || (check && ((key & mask) == key_space))) {
                spin1_send_mc_packet(key, 0, NO_PAYLOAD);
            } else {
                incorrect_keys++;
            }
        }
    } else if (!payload && pkt_payload_prefix_apply) {
        log_debug("16 bit, fixed payload");

        uint16_t *events_array = (uint16_t *) event_pointer;
        uint32_t payload = pkt_payload_prefix;

        for (i = 0; i < length; i++) {
            uint32_t key = (uint32_t) (events_array[i]);

            if (!pkt_format) {
                key <<= 16;
            }
            key |= pkt_prefix;

            log_debug("mc packet 16 key: %08x, payload: %08x", key, payload);
            log_debug("check before send packet: %d",
                    (!check) || (check && ((key & mask) == key_space)));

            if ((!check) || (check && ((key & mask) == key_space))) {
                spin1_send_mc_packet(key, payload, WITH_PAYLOAD);
            } else {
                incorrect_keys++;
            }
        }
    } else {
        log_debug("16 bit, with payload");

        event16_t *events_struct = (event16_t *) event_pointer;

        for (i = 0; i < length; i++) {
            uint32_t payload = (uint32_t) events_struct[i].payload;
            uint32_t key = (uint32_t) events_struct[i].event;

            if (!pkt_format) {
                key <<= 16;
            }
            key |= pkt_prefix;
            payload |= pkt_payload_prefix;

            log_debug("mc packet 16 key: %08x, payload: %08x", key, payload);
            log_debug("check before send packet: %d",
                    (!check) || (check && ((key & mask) == key_space)));

            if ((!check) || (check && ((key & mask) == key_space))) {
                spin1_send_mc_packet(key, payload, WITH_PAYLOAD);
            } else {
                incorrect_keys++;
            }
        }
    }
}

void process_32_bit_packets(
        void* event_pointer, uint32_t length, uint32_t pkt_prefix,
        uint32_t pkt_payload_prefix, bool payload,
        bool pkt_payload_prefix_apply) {
    uint32_t i;

    log_debug("process_32_bit_packets");
    log_debug("event_pointer: %08x", (uint32_t) event_pointer);
    log_debug("length: %d", length);
    log_debug("pkt_prefix: %08x", pkt_prefix);
    log_debug("pkt_payload_prefix: %08x", pkt_payload_prefix);
    log_debug("payload: %d", payload);
    log_debug("pkt_payload_prefix_apply: %d", pkt_payload_prefix_apply);

    if (!payload && !pkt_payload_prefix_apply) {
        log_debug("32 bit, no payload");

        uint16_t *events = (uint16_t *) event_pointer;

        for (i = 0; i < (length << 1); i += 2) {
            uint32_t key;
            uint32_t temp1 = events[i];
            uint32_t temp2 = events[i + 1];

            key = temp2 << 16 | temp1;
            key |= pkt_prefix;

            log_debug("mc packet 32 key: %08x", key);
            log_debug("check before send packet: %d",
                    (!check) || (check && ((key & mask) == key_space)));

            if ((!check) || (check && ((key & mask) == key_space))) {
                spin1_send_mc_packet(key, 0, NO_PAYLOAD);
            } else {
                incorrect_keys++;
            }
        }
    } else if (!payload && pkt_payload_prefix_apply) {
        log_debug("32 bit, fixed payload");

        uint16_t *events = (uint16_t *) event_pointer;
        uint32_t payload = pkt_payload_prefix;

        for (i = 0; i < (length << 1); i += 2) {
            uint32_t key;
            uint32_t temp1 = events[i];
            uint32_t temp2 = events[i + 1];

            key = temp2 << 16 | temp1;
            key |= pkt_prefix;

            log_debug("mc packet 32 key: %08x, payload: %08x", key, payload);
            log_debug("check before send packet: %d",
                    (!check) || (check && ((key & mask) == key_space)));

            if ((!check) || (check && ((key & mask) == key_space))) {
                spin1_send_mc_packet(key, payload, WITH_PAYLOAD);
            } else {
                incorrect_keys++;
            }
        }
    } else {
        log_debug("32 bit, with payload");

        uint16_t *events = (uint16_t *) event_pointer;

        for (i = 0; i < (length << 2); i += 4) {
            uint32_t key;
            uint32_t payload;

            uint32_t temp1 = events[i];
            uint32_t temp2 = events[i + 1];
            key = temp2 << 16 | temp1;
            key |= pkt_prefix;

            temp1 = events[i + 2];
            temp2 = events[i + 3];
            payload = temp2 << 16 | temp1;
            payload |= pkt_payload_prefix;

            log_debug("mc packet 32 key: %08x, payload: %08x", key, payload);
            log_debug("check before send packet: %d",
                    (!check) || (check && ((key & mask) == key_space)));

            if ((!check) || (check && ((key & mask) == key_space))) {
                spin1_send_mc_packet(key, payload, WITH_PAYLOAD);
            } else {
                incorrect_keys++;
            }
        }
    }
}

void sdp_packet_callback(uint mailbox, uint port) {
    use(port);

    log_debug("\n");
    log_debug("====================================");

    sdp_msg_t *msg = (sdp_msg_t *) mailbox;
    uint16_t *data_hdr = (uint16_t *) &(msg->cmd_rc);
    uint16_t data_hdr_value = data_hdr[0];
    void *event_pointer = (void *) (data_hdr + 1);

#if LOG_LEVEL >= LOG_DEBUG
    log_debug("data_hdr: %08x", (uint32_t) data_hdr);
    log_debug("event_pointer: %08x", (uint32_t) event_pointer);

    uint32_t len = msg -> length + 8;
    uint8_t *ptr = (uint8_t *) msg;

    log_debug("packet lenght: %d", len);
    for (uint32_t i = 0; i < len; i++) {
        log_debug(" %02x", ptr[i]);
    }
#endif

    bool pkt_apply_prefix = (bool) (data_hdr_value >> 15);
    bool pkt_format = (bool) (data_hdr_value >> 14 & 0x1);
    bool pkt_payload_prefix_apply = (bool) (data_hdr_value >> 13 & 0x1);
    bool pkt_timestamp = (bool) (data_hdr_value >> 12 & 0x1);
    uint8_t pkt_type = (uint8_t) (data_hdr_value >> 10 & 0x3);
    uint8_t pkt_len = (uint8_t) (data_hdr_value & 0xFF);
    bool payload_on = (bool) (pkt_type & 0x1);
    uint32_t pkt_key_prefix = prefix;
    uint32_t pkt_payload_prefix = 0;

    log_debug("data_hdr_value: %04x", data_hdr_value);
    log_debug("pkt_apply_prefix: %d", pkt_apply_prefix);
    log_debug("pkt_format: %d", pkt_format);
    log_debug("pkt_payload_prefix: %d", pkt_payload_prefix_apply);
    log_debug("pkt_timestamp: %d", pkt_timestamp);
    log_debug("pkt_type: %d", pkt_type);
    log_debug("pkt_len: %d", pkt_len);
    log_debug("payload_on: %d", payload_on);

    if (pkt_apply_prefix) {
        uint16_t *key_prefix_ptr = (uint16_t *) event_pointer;
        event_pointer = (void*) (((uint16_t *) event_pointer) + 1);

        pkt_key_prefix = (uint32_t) key_prefix_ptr[0];

        if (pkt_format) {
            pkt_key_prefix <<= 16;
        }
    } else if (!pkt_apply_prefix && apply_prefix) {
        if (key_left_shift == 0) {
            pkt_format = 1;
        } else {
            pkt_format = 0;
        }
    }

    if (pkt_payload_prefix_apply) {
        if (!(pkt_type & 0x2)) {

            //16 bit type packet
            uint16_t *payload_prefix_ptr = (uint16_t *) event_pointer;
            event_pointer = (void*) (((uint16_t *) event_pointer) + 1);

            pkt_payload_prefix = (uint32_t) payload_prefix_ptr[0];
        } else {

            //32 bit type packet
            uint16_t *payload_prefix_ptr = (uint16_t *) event_pointer;
            event_pointer = (void*) (((uint16_t *) event_pointer) + 2);

            uint32_t temp1 = payload_prefix_ptr[0];
            uint32_t temp2 = payload_prefix_ptr[1];
            pkt_payload_prefix = temp2 << 16 | temp1;
        }
    }

    if (pkt_type <= 1) {
        process_16_bit_packets(event_pointer, pkt_format, pkt_len,
                pkt_key_prefix, pkt_payload_prefix, payload_on,
                pkt_payload_prefix_apply);
    } else {
        process_32_bit_packets(event_pointer, pkt_len, pkt_key_prefix,
                pkt_payload_prefix, payload_on, pkt_payload_prefix_apply);
    }

    //free the message to stop overload
    spin1_msg_free(msg);
}

void read_parameters(address_t region_address) {

    apply_prefix = region_address[0];
    prefix = region_address[1];
    key_left_shift = region_address[2];
    check = region_address[3];
    key_space = region_address[4];
    mask = region_address[5];

    incorrect_keys = 0;

    log_info("apply_prefix: %d", apply_prefix);
    log_info("prefix: %d", prefix);
    log_info("key_left_shift: %d", key_left_shift);
    log_info("check: %d", check);
    log_info("key_space: %08x", key_space);
    log_info("mask: %08x", mask);
}

bool initialize(uint32_t *timer_period) {

    // Get the address this core's DTCM data starts at from SRAM
    address_t address = data_specification_get_data_address();

    // Read the header
    uint32_t version;
    if (!data_specification_read_header(address, &version)) {
        return false;
    }

    // Get the timing details
    if (!simulation_read_timing_details(
            data_specification_get_region(0, address),
            APPLICATION_MAGIC_NUMBER, timer_period, &simulation_ticks)) {
        return false;
    }

    // Read the parameters
    read_parameters(data_specification_get_region(1, address));

    return true;
}


// Entry point
void c_main(void) {

    // Configure system
    uint32_t timer_period = 0;
    if (!initialize(&timer_period)) {
        return;
    }

    // Set timer_callback
    spin1_set_timer_tick(timer_period);

    // Register callbacks
    spin1_callback_on(SDP_PACKET_RX, sdp_packet_callback, -1);
    spin1_callback_on(TIMER_TICK, timer_callback, 2);

    log_info("Starting");

    // Start the time at "-1" so that the first tick will be 0
    time = UINT32_MAX;
    simulation_run();
}
