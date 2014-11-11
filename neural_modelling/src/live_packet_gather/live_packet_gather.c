#include <common-typedefs.h>
#include <data_specification.h>
#include <debug.h>
#include <simulation.h>
#include <spin1_api.h>

#define APPLICATION_MAGIC_NUMBER 0xAC0

// Globals
static sdp_msg_t g_event_message;
static uint16_t *sdp_msg_aer_header;
static uint16_t *sdp_msg_aer_key_prefix;
static void *sdp_msg_aer_payload_prefix;
static void *sdp_msg_aer_data;
static uint32_t time;
static uint32_t packets_sent;
static uint32_t buffer_index;
static uint16_t temp_header;
static uint8_t event_size;
static uint8_t header_len;
static uint32_t simulation_ticks = 0;

static uint32_t apply_prefix;			// P bit
static uint32_t prefix;					// Prefix data
static uint32_t packet_type;			// Type bits
static uint32_t prefix_type;			// F bit (for the receiver)
static uint32_t key_right_shift;		// Right payload shift (for the sender)
static uint32_t payload_timestamp;		// T bit
static uint32_t payload_apply_prefix;	// D bit
static uint32_t payload_prefix;		    // Payload prefix data (for the rcvr)
static uint32_t payload_right_shift;	// Right payload shift (for the sender)
static uint32_t sdp_tag;
static uint32_t packets_per_timestamp;

void flush_events(void) {

    // Send the event message only if there is data
    if (buffer_index > 0) {
        uint8_t event_count;
        uint16_t bytes_to_clear = 0;

        if ((packets_per_timestamp == 0)
                || (packets_sent < packets_per_timestamp)) {

            // Get the event count depending on if there is a payload or not
            if (packet_type & 0x1) {
                event_count = buffer_index >> 1;
            } else {
                event_count = buffer_index;
            }

            // insert appropriate header
            sdp_msg_aer_header[0] = 0;
            sdp_msg_aer_header[0] |= temp_header;
            sdp_msg_aer_header[0] |= (event_count & 0xff);

            g_event_message.length = sizeof(sdp_hdr_t) + header_len
                    + event_count * event_size;

#if LOG_LEVEL >= LOG_DEBUG
            log_debug("===========Packet============\n");
            uint8_t *print_ptr = (uint8_t *) &g_event_message;
            for (uint8_t i = 0; i < g_event_message.length + 8; i++) {
                log_debug("%02x ", print_ptr[i]);
            }
#endif // DEBUG

            if (payload_apply_prefix && payload_timestamp) {
                uint16_t *temp = (uint16_t *) sdp_msg_aer_payload_prefix;

                if (!(packet_type && 0x2)) {
                    temp[0] = (time & 0xFFFF);
                } else {
                    temp[0] = (time & 0xFFFF);
                    temp[1] = ((time >> 16) & 0xFFFF);
                }
            }

#if LOG_LEVEL >= LOG_DEBUG
            log_debug("===========Packet============\n");
            uint8_t *print_ptr = (uint8_t *) &sdp_msg_aer_data;
            for (uint8_t i = 0; i < buffer_index * event_size; i++) {
                log_debug("%02x ", print_ptr[i]);
            }
#endif // DEBUG

            spin1_send_sdp_msg(&g_event_message, 1);
            packets_sent++;
        }

        // reset packet content
        bytes_to_clear = buffer_index * event_size;
        uint16_t *temp = (uint16_t *) sdp_msg_aer_data;
        for (uint8_t i = 0; i < (bytes_to_clear >> 2); i++) {
            temp[i] = 0;
        }
    }

    // reset counter
    buffer_index = 0;
}

// Callbacks
void timer_callback(uint unused0, uint unused1) {
    use(unused0);
    use(unused1);

    // flush the spike message and sent it over the ethernet
    flush_events();

    // increase time variable to keep track of current timestep
    time++;
    log_debug("Timer tick %u", time);

    // check if the simulation has run to completion
    if ((simulation_ticks != UINT32_MAX) && (time >= simulation_ticks)) {
        log_info("Simulation complete.\n");
        spin1_exit(0);
    }
}

void flush_events_if_full(void) {
    uint8_t event_count;

    if (packet_type & 0x1) {
        event_count = buffer_index >> 1;
    } else {
        event_count = buffer_index;
    }

    if (((event_count + 1) * event_size) > 256) {
        flush_events();
    }
}

// callback for mc packet without payload
void incoming_event_callback(uint key, uint payload) {
    use(payload);
    log_debug("Received event with key %x", key);

    // process the received spike
    uint16_t *buf_pointer = (uint16_t *) sdp_msg_aer_data;
    if (!(packet_type & 0x2)) {

        // 16 bit packet
        buf_pointer[buffer_index] = (key >> key_right_shift) & 0xFFFF;
        buffer_index++;

        // if there is a payload to be added
        if ((packet_type & 0x1) && (!payload_timestamp)) {
            buf_pointer[buffer_index] = 0;
            buffer_index++;
        } else if ((packet_type & 0x1) && payload_timestamp) {
            buf_pointer[buffer_index] = (time & 0xFFFF);
            buffer_index++;
        }
    } else {

        // 32 bit packet
        uint16_t spike_index = buffer_index << 1;

        buf_pointer[spike_index] = (key & 0xFFFF);
        buf_pointer[spike_index + 1] = ((key >> 16) & 0xFFFF);
        buffer_index++;

        // if there is a payload to be added
        if ((packet_type & 0x1) && (!payload_timestamp)) {
            spike_index = buffer_index << 1;
            buf_pointer[spike_index] = 0;
            buf_pointer[spike_index + 1] = 0;
            buffer_index++;
        } else if ((packet_type & 0x1) && payload_timestamp) {
            spike_index = buffer_index << 1;
            buf_pointer[spike_index] = (time & 0xFFFF);
            buf_pointer[spike_index + 1] = ((time >> 16) & 0xFFFF);
            buffer_index++;
        }
    }

    // send packet if enough data is stored
    flush_events_if_full();
}

// callback for mc packet with payload
void incoming_event_payload_callback(uint key, uint payload) {
    log_debug("Received spike %x", key);

    // process the received spike
    uint16_t *buf_pointer = (uint16_t *) sdp_msg_aer_data;
    if (!(packet_type & 0x2)) {

        //16 bit packet
        buf_pointer[buffer_index] = (key >> key_right_shift) & 0xFFFF;
        buffer_index++;

        //if there is a payload to be added
        if ((packet_type & 0x1) && (!payload_timestamp)) {
            buf_pointer[buffer_index] = (payload >> payload_right_shift)
                    & 0xFFFF;
            buffer_index++;
        } else if ((packet_type & 0x1) && payload_timestamp) {
            buf_pointer[buffer_index] = (time & 0xFFFF);
            buffer_index++;
        }
    } else {

        //32 bit packet
        uint16_t spike_index = buffer_index << 1;

        buf_pointer[spike_index] = (key & 0xFFFF);
        buf_pointer[spike_index + 1] = ((key >> 16) & 0xFFFF);
        buffer_index++;

        //if there is a payload to be added
        if ((packet_type & 0x1) && !payload_timestamp){
            spike_index = buffer_index << 1;
            buf_pointer[spike_index] = (payload & 0xFFFF);
            buf_pointer[spike_index + 1] = ((payload >> 16) & 0xFFFF);
            buffer_index++;
        } else if ((packet_type & 0x1) && payload_timestamp) {
            spike_index = buffer_index << 1;
            buf_pointer[spike_index] = (time & 0xFFFF);
            buf_pointer[spike_index + 1] = ((time >> 16) & 0xFFFF);
            buffer_index++;
        }
    }

    // send packet if enough data is stored
    flush_events_if_full();
}

void read_parameters(address_t region_address) {

    apply_prefix = region_address[0];         // P bit
    prefix = region_address[1];               // Prefix data
    prefix_type = region_address[2];          // F bit (for the receiver)
    packet_type = region_address[3];          // Type bits
    key_right_shift = region_address[4];      // Right packet shift
                                              //     (for the sender)
    payload_timestamp = region_address[5];    // T bit
    payload_apply_prefix = region_address[6]; // D bit
    payload_prefix = region_address[7];	      // Payload prefix data
                                              //     (for the receiver)
    payload_right_shift = region_address[8];  // Right payload shift
                                              //     (for the sender)
    sdp_tag = region_address[9];
    packets_per_timestamp = region_address[10];

    log_info("apply_prefix: %d\n", apply_prefix);
    log_info("prefix: %08x\n", prefix);
    log_info("prefix_type: %d\n", prefix_type);
    log_info("packet_type: %d\n", packet_type);
    log_info("key_right_shift: %d\n", key_right_shift);
    log_info("payload_timestamp: %d\n", payload_timestamp);
    log_info("payload_apply_prefix: %d\n", payload_apply_prefix);
    log_info("payload_prefix: %08x\n", payload_prefix);
    log_info("payload_right_shift: %d\n", payload_right_shift);
    log_info("sdp_tag: %d\n", sdp_tag);
    log_info("packets_per_timestamp: %d\n", packets_per_timestamp);
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

    // Fix simulation ticks to be one extra timer period to soak up last events
    if (simulation_ticks != UINT32_MAX) {
        simulation_ticks += *timer_period;
    }

    // Read the parameters
    read_parameters(data_specification_get_region(1, address));

    return true;
}

bool configure_sdp_msg(void) {
    log_info("configure_sdp_msg\n");

    void *temp_ptr;

    temp_header = 0;
    event_size = 0;

    // initialize SDP header
    g_event_message.tag = sdp_tag; // Arbitrary tag
    g_event_message.flags = 0x07; // No reply required

    g_event_message.dest_addr = 0; // Chip 0,0
    g_event_message.dest_port = PORT_ETH; // Dump through Ethernet

    // Set up monitoring address and port
    g_event_message.srce_addr = spin1_get_chip_id();
    g_event_message.srce_port = (3 << PORT_SHIFT) | spin1_get_core_id();

    // check incompatible options
    if (payload_timestamp && payload_apply_prefix && (packet_type & 0x1)) {
        log_error("Timestamp can either be included as payload prefix or as"
                "payload to each key, not both\n");
        return false;
    }
    if (payload_timestamp && !payload_apply_prefix && !(packet_type & 0x1)) {
        log_error("Timestamp can either be included as payload prefix or as"
                "payload to each key, but current configuration does not"
                "specify either of these\n");
        return false;
    }

    // initialize AER header
    sdp_msg_aer_header = &g_event_message.cmd_rc; // pointer to data space

    temp_header |= (apply_prefix << 15);
    temp_header |= (prefix_type << 14);
    temp_header |= (payload_apply_prefix << 13);
    temp_header |= (payload_timestamp << 12);
    temp_header |= (packet_type << 10);

    header_len = 2;
    temp_ptr = (void *) sdp_msg_aer_header[1];

    // pointers for AER packet header, prefix(es) and data
    if (apply_prefix) {

        // pointer to key prefix
        sdp_msg_aer_key_prefix = (sdp_msg_aer_header + 1);
        temp_ptr = (void *) (sdp_msg_aer_header + 2);
        sdp_msg_aer_key_prefix[0] = (uint16_t) prefix;
        header_len += 2;
    } else {
        sdp_msg_aer_key_prefix = NULL;
        temp_ptr = (void *) (sdp_msg_aer_header + 1);
    }

    if (payload_apply_prefix) {
        sdp_msg_aer_payload_prefix = temp_ptr;
        uint16_t *a = (uint16_t *) sdp_msg_aer_payload_prefix;

        log_debug("temp_ptr: %08x\n", (uint32_t) temp_ptr);
        log_debug("a: %08x\n", (uint32_t) a);
        sdp_msg_aer_payload_prefix = temp_ptr; // pointer to payload prefix

        if (!(packet_type & 0x2)) {

            //16 bit payload prefix
            temp_ptr = (void *) (a + 1);
            header_len += 2;
            if (!payload_timestamp) {

                // add payload prefix as required - not a timestamp
                a[0] = payload_prefix;
            }
            log_debug("16 bit - temp_ptr: %08x\n", (uint32_t) temp_ptr);

        } else {

            //32 bit payload prefix
            temp_ptr = (void *) (a + 2);
            header_len += 4;
            if (!payload_timestamp) {
                // add payload prefix as required - not a timestamp
                a[0] = (payload_prefix & 0xFFFF);
                a[1] = ((payload_prefix >> 16) & 0xFFFF);
            }
            log_debug("32 bit - temp_ptr: %08x\n", (uint32_t) temp_ptr);
        }
    } else {
        sdp_msg_aer_payload_prefix = NULL;
    }

    sdp_msg_aer_data = (void *) temp_ptr; // pointer to write data

    switch (packet_type) {
    case 0:
        event_size = 2;
        break;

    case 1:
        event_size = 4;
        break;

    case 2:
        event_size = 4;
        break;

    case 3:
        event_size = 8;
        break;

    default:
        log_error("unknown packet type: %d\n", packet_type);
        return false;
    }

    log_debug("sdp_msg_aer_header: %08x\n", (uint32_t) sdp_msg_aer_header);
    log_debug("sdp_msg_aer_key_prefix: %08x\n",
            (uint32_t) sdp_msg_aer_key_prefix);
    log_debug("sdp_msg_aer_payload_prefix: %08x\n",
            (uint32_t) sdp_msg_aer_payload_prefix);
    log_debug("sdp_msg_aer_data: %08x\n", (uint32_t) sdp_msg_aer_data);

    packets_sent = 0;
    buffer_index = 0;

    return true;
}

// Entry point
void c_main(void) {

    // Configure system
    uint32_t timer_period = 0;
    if (!initialize(&timer_period)) {
        return;
    }

    // Configure SDP message
    if (!configure_sdp_msg()) {
        return;
    }

    // Set timer_callback
    spin1_set_timer_tick(timer_period);

    // Register callbacks
    spin1_callback_on(MC_PACKET_RECEIVED, incoming_event_callback, -1);
    spin1_callback_on(MCPL_PACKET_RECEIVED,
            incoming_event_payload_callback,-1);
    spin1_callback_on(TIMER_TICK, timer_callback, 2);

    log_info("Starting\n");

    // Start the time at "-1" so that the first tick will be 0
    time = UINT32_MAX;
    simulation_run();
}
