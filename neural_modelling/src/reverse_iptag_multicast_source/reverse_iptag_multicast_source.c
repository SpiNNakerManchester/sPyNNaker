#include <common-typedefs.h>
#include <data_specification.h>
#include <debug.h>
#include <simulation.h>
#include <sark.h>
#include <string.h>

#define APPLICATION_MAGIC_NUMBER 0xAC9

// Database handshake with visualiser
#define DATABASE_CONFIRMATION 1

// Fill in buffer area with padding
#define EVENT_PADDING 2

// End of all buffers, stop execution
#define EVENT_STOP 3

// Stop complaining that there is sdram free space for buffers
#define STOP_SENDING_REQUESTS 4

// Start complaining that there is sdram free space for buffers
#define START_SENDING_REQUESTS 5

// Spinnaker requesting new buffers for spike source population
#define SPINNAKER_REQUEST_BUFFERS 6

// Buffers being sent from host to SpiNNaker
#define HOST_SEND_SEQUENCED_DATA 7

// Buffers available to be read from a buffered out vertex
#define SPINNAKER_REQUEST_READ_DATA 8

// Host confirming data being read form SpiNNaker memory
#define HOST_DATA_READ 9

#define BUFFER_OPERATION_READ 0
#define BUFFER_OPERATION_WRITE 1

#define BUFFER_REGION 2
#define MIN_BUFFER_SPACE 10

// The maximum sequence number
#define MAX_SEQUENCE_NO 0xFF

#pragma pack(1)

typedef uint16_t* eieio_msg_t;

typedef struct {
    uint16_t event;
    uint16_t payload;
} event16_t;

typedef struct {
    uint16_t eieio_header_command;
    uint16_t chip_id;
    uint8_t processor;
    uint8_t pad1;
    uint8_t region;
    uint8_t sequence;
    uint32_t space_available;
} req_packet_sdp_t;

// Globals
static uint32_t time;
static uint32_t simulation_ticks;

static bool apply_prefix;
static bool check;
static uint32_t prefix;
static uint32_t key_space;
static uint32_t mask;
static uint32_t incorrect_keys;
static uint32_t incorrect_packets;
static uint32_t key_left_shift;
static uint32_t buffer_region_size;
static uint32_t space_before_data_request;

static uint8_t *buffer_region;
static uint8_t *end_of_buffer_region;
static uint8_t *write_pointer;
static uint8_t *read_pointer;

sdp_msg_t req;
req_packet_sdp_t *req_ptr;
static eieio_msg_t msg_from_sdram;
static bool msg_from_sdram_in_use;
static uint32_t next_buffer_time;
static uint8_t pkt_last_sequence_seen;
static bool send_ack_last_state;
static bool send_packet_reqs;
static bool last_buffer_operation;
static uint8_t return_tag_id;
static uint32_t last_space;


static inline uint16_t calculate_eieio_packet_command_size(
        eieio_msg_t eieio_msg_ptr) {
    uint16_t data_hdr_value = eieio_msg_ptr[0];
    uint16_t command_number = data_hdr_value & ~0xC000;

    switch (command_number) {
    case DATABASE_CONFIRMATION:
    case EVENT_PADDING:
    case EVENT_STOP:
    case STOP_SENDING_REQUESTS:
    case START_SENDING_REQUESTS:
        return 2;
    case SPINNAKER_REQUEST_BUFFERS:
        return 12;
    case HOST_SEND_SEQUENCED_DATA:

        // does not include the eieio packet payload
        return 4;
    case SPINNAKER_REQUEST_READ_DATA:
        return 16;
    case HOST_DATA_READ:
        return 8;
    default:
        return 0;
    }
    return 0;
}

static inline uint16_t calculate_eieio_packet_event_size(
        eieio_msg_t eieio_msg_ptr) {
    uint16_t data_hdr_value = eieio_msg_ptr[0];
    uint8_t pkt_type = (uint8_t)(data_hdr_value >> 10 & 0x3);
    bool pkt_apply_prefix = (bool)(data_hdr_value >> 15);
    bool pkt_payload_prefix_apply = (bool)(data_hdr_value >> 13 & 0x1);
    uint8_t event_count = data_hdr_value & 0xFF;
    uint16_t event_size, total_size;
    uint16_t header_size = 2;

    switch (pkt_type) {
    case 0:
        event_size = 2;
        break;
    case 1:
    case 2:
        event_size = 4;
        break;
    case 3:
        event_size = 8;
        break;
    }

    if (pkt_apply_prefix) {
        header_size += 2;
    }
    if (pkt_payload_prefix_apply) {
        if (pkt_type == 0 || pkt_type == 1) {
            header_size += 2;
        } else {
            header_size += 4;
        }
    }

    total_size = event_count * event_size + header_size;
    return total_size;
}

static inline uint16_t calculate_eieio_packet_size(eieio_msg_t eieio_msg_ptr) {
    uint16_t data_hdr_value = eieio_msg_ptr[0];
    uint8_t pkt_type = (data_hdr_value >> 14) && 0x03;

    if (pkt_type == 0x01) {
        return calculate_eieio_packet_command_size(eieio_msg_ptr);
    } else {
        return calculate_eieio_packet_event_size(eieio_msg_ptr);
    }
}

static inline void print_packet_bytes(eieio_msg_t eieio_msg_ptr,
                                      uint16_t length) {
    use(eieio_msg_ptr);
    use(length);
#if LOG_LEVEL >= LOG_DEBUG
    uint8_t *ptr = (uint8_t *) eieio_msg_ptr;

    log_debug("packet of %d bytes:", length);

    for (int i = 0; i < length; i++) {
        if ((i & 7) == 0) {
            io_printf(IO_BUF, "\n");
        }
        io_printf(IO_BUF, "%02x", ptr[i]);
    }
    io_printf(IO_BUF, "\n");
#endif
}

static inline void print_packet(eieio_msg_t eieio_msg_ptr) {
    use(eieio_msg_ptr);
#if LOG_LEVEL >= LOG_DEBUG
    uint32_t len = calculate_eieio_packet_size(eieio_msg_ptr);
    print_packet_bytes(eieio_msg_ptr, len);
#endif
}

static inline void signal_software_error(eieio_msg_t eieio_msg_ptr,
                                         uint16_t length) {
#if LOG_LEVEL >= LOG_DEBUG
    print_packet_bytes(eieio_msg_ptr, length);
    rt_error(RTE_SWERR);
#endif
}

static inline uint32_t get_sdram_buffer_space_available() {
    if (read_pointer < write_pointer) {
        uint32_t final_space = (uint32_t) end_of_buffer_region -
                               (uint32_t) write_pointer;
        uint32_t initial_space = (uint32_t) read_pointer -
                                 (uint32_t) buffer_region;
        return final_space + initial_space;
    } else if (write_pointer < read_pointer) {
        return (uint32_t) read_pointer - (uint32_t) write_pointer;
    } else if (last_buffer_operation == BUFFER_OPERATION_WRITE) {

        // If pointers are equal, buffer is full if last op is write
        return 0;
    } else {

        // If pointers are equal, buffer is empty if last op is read
        return buffer_region_size;
    }
}

static inline bool is_eieio_packet_in_buffer(void) {
    uint32_t write_ptr_value = (uint32_t) write_pointer;
    uint32_t read_ptr_value = (uint32_t) read_pointer;

    // If there is no buffering being done, there are no packets
    if (buffer_region_size == 0) {
        return false;
    }

    // There are packets as long as the buffer is not empty; the buffer is
    // empty if the pointers are equal and the last op was read
    return !((write_pointer == read_pointer) &&
            (last_buffer_operation == BUFFER_OPERATION_READ));
}

static inline uint32_t extract_time_from_eieio_msg(eieio_msg_t eieio_msg_ptr) {
    uint16_t data_hdr_value = eieio_msg_ptr[0];
    bool pkt_has_timestamp = (bool) (data_hdr_value >> 12 & 0x1);
    bool pkt_apply_prefix = (bool) (data_hdr_value >> 15);
    bool pkt_mode = data_hdr_value >> 14;

    // If the packet is actually a command packet, return the current time
    if (pkt_apply_prefix == 0 && pkt_mode == 1) {
        return time;
    }

    // If the packet indicates that payloads are timestamps
    if (pkt_has_timestamp) {
        bool pkt_payload_prefix_apply = (bool) (data_hdr_value >> 13 & 0x1);
        uint8_t pkt_type = (uint8_t) (data_hdr_value >> 10 & 0x3);
        uint32_t payload_time = 0;
        bool got_payload_time = false;
        uint16_t *event_ptr = &eieio_msg_ptr[1];

        // If there is a payload prefix
        if (pkt_payload_prefix_apply) {

            uint16_t *payload_prefix;

            // If there is a key prefix, the payload prefix is after that
            if (pkt_apply_prefix) {
                event_ptr += 1;
            }

            if (pkt_type & 0x2) {

                // 32 bit packet
                payload_time = *(event_ptr++) << 16 | *(event_ptr++);
            } else {

                // 16 bit packet
                payload_time = *(event_ptr++);
            }
            got_payload_time = true;
        }

        // If the packets have a payload
        if (pkt_type & 0x1) {
            if (pkt_type & 0x2) {

                // 32 bit packet
                payload_time |= *(event_ptr++) << 16 | *(event_ptr++);
            } else {

                // 16 bit packet
                payload_time |= *(event_ptr++);
            }
            got_payload_time = true;
        }

        // If no actual time was found, return the current time
        if (!got_payload_time) {
            return time;
        }
        return payload_time;
    }

    // This is not a timed packet, return the current time
    return time;
}

static inline bool add_eieio_packet_to_sdram(
        eieio_msg_t eieio_msg_ptr, uint32_t length) {
    uint8_t *msg_ptr = (uint8_t *) eieio_msg_ptr;

    log_debug("read_pointer = 0x%.8x, write_pointer= = 0x%.8x,"
              "last_buffer_operation == read = %d, packet length = %d",
              read_pointer,  write_pointer,
              last_buffer_operation == BUFFER_OPERATION_READ, length);
    if ((read_pointer < write_pointer) ||
            (read_pointer == write_pointer &&
                last_buffer_operation == BUFFER_OPERATION_READ)) {
        uint32_t final_space = (uint32_t) end_of_buffer_region -
                               (uint32_t) write_pointer;

        if (final_space >= length) {
            log_debug("Packet fits in final space of %d", final_space);

            spin1_memcpy(write_pointer, msg_ptr, length);
            write_pointer += length;
            last_buffer_operation = BUFFER_OPERATION_WRITE;
            if (write_pointer >= end_of_buffer_region) {
                write_pointer = buffer_region;
            }
            return true;
        } else {

            uint32_t total_space = final_space + ((uint32_t) read_pointer -
                                                  (uint32_t) buffer_region);
            if (total_space < length) {
                log_debug("Not enough space (%d bytes)", total_space);
                return false;
            }

            log_debug("Copying first %d bytes to final space of %d",
                      final_space);
            spin1_memcpy(write_pointer, msg_ptr, final_space);
            write_pointer = buffer_region;
            msg_ptr += final_space;

            uint32_t final_len = length - final_space;
            log_debug("Copying remaining %d bytes", final_len);
            spin1_memcpy(write_pointer, msg_ptr, final_len);
            write_pointer += final_len;
            last_buffer_operation = BUFFER_OPERATION_WRITE;
            if (write_pointer == end_of_buffer_region) {
                write_pointer = buffer_region;
            }
            return true;
        }
    } else if (write_pointer < read_pointer) {
        uint32_t middle_space = (uint32_t) read_pointer -
                                (uint32_t) write_pointer;

        if (middle_space < length) {
            log_debug("Not enough space in middle (%d bytes)", middle_space);
            return false;
        } else {
            log_debug("Packet fits in middle space of %d", middle_space);
            spin1_memcpy(write_pointer, msg_ptr, length);
            write_pointer += length;
            last_buffer_operation = BUFFER_OPERATION_WRITE;
            if (write_pointer == end_of_buffer_region) {
                write_pointer = buffer_region;
            }
            return true;
        }
    }

    log_debug("Buffer already full");
    return false;
}

static inline void process_16_bit_packets(
        void* event_pointer, bool pkt_prefix_upper, uint32_t pkt_count,
        uint32_t pkt_key_prefix, uint32_t pkt_payload_prefix,
        bool pkt_has_payload, bool pkt_payload_is_timestamp) {

    log_debug("process_16_bit_packets");
    log_debug("event_pointer: %08x", (uint32_t) event_pointer);
    log_debug("count: %d", pkt_count);
    log_debug("pkt_prefix: %08x", pkt_key_prefix);
    log_debug("pkt_payload_prefix: %08x", pkt_payload_prefix);
    log_debug("payload on: %d", pkt_has_payload);
    log_debug("pkt_format: %d", pkt_prefix_upper);

    uint16_t *next_event = (uint16_t *) event_pointer;
    for (uint32_t i = 0; i < pkt_count; i++) {
        uint32_t key = (uint32_t) *(next_event++);
        uint32_t payload = 0;
        if (pkt_has_payload) {
            payload = (uint32_t) *(next_event++);
        }

        if (!pkt_prefix_upper) {
            key <<= 16;
        }
        key |= pkt_key_prefix;
        payload |= pkt_payload_prefix;

        log_debug("check before send packet: %d",
                  (!check) || (check && ((key & mask) == key_space)));

        if (!check || (check && ((key & mask) == key_space))) {
            if (pkt_has_payload && !pkt_payload_is_timestamp) {
                log_debug("mc packet 16-bit key=%d", key);
                spin1_send_mc_packet(key, payload, WITH_PAYLOAD);
            } else {
                log_debug("mc packet 16-bit key=%d, payload=%d", key, payload);
                spin1_send_mc_packet(key, 0, NO_PAYLOAD);
            }
        } else {
            incorrect_keys++;
        }
    }
}

static inline void process_32_bit_packets(
        void* event_pointer, bool pkt_prefix_upper, uint32_t pkt_count,
        uint32_t pkt_key_prefix, uint32_t pkt_payload_prefix,
        bool pkt_has_payload, bool pkt_payload_is_timestamp) {

    log_debug("process_16_bit_packets");
    log_debug("event_pointer: %08x", (uint32_t) event_pointer);
    log_debug("count: %d", pkt_count);
    log_debug("pkt_prefix: %08x", pkt_key_prefix);
    log_debug("pkt_payload_prefix: %08x", pkt_payload_prefix);
    log_debug("payload on: %d", pkt_has_payload);
    log_debug("pkt_format: %d", pkt_prefix_upper);

    uint32_t *next_event = (uint32_t *) event_pointer;
    for (uint32_t i = 0; i < pkt_count; i++) {
        uint32_t key = *(next_event++);
        uint32_t payload = 0;
        if (pkt_has_payload) {
            payload = *(next_event++);
        }

        if (!pkt_prefix_upper) {
            key <<= 16;
        }
        key |= pkt_key_prefix;
        payload |= pkt_payload_prefix;

        log_debug("check before send packet: %d",
                  (!check) || (check && ((key & mask) == key_space)));

        if (!check || (check && ((key & mask) == key_space))) {
            if (pkt_has_payload && !pkt_payload_is_timestamp) {
                log_debug("mc packet 32-bit key=%d", key);
                spin1_send_mc_packet(key, payload, WITH_PAYLOAD);
            } else {
                log_debug("mc packet 32-bit key=%d, payload=%d", key, payload);
                spin1_send_mc_packet(key, 0, NO_PAYLOAD);
            }
        } else {
            incorrect_keys++;
        }
    }
}

static inline bool eieio_data_parse_packet(
        eieio_msg_t eieio_msg_ptr, uint32_t length) {
    log_debug("eieio_data_process_data_packet");
    print_packet_bytes(eieio_msg_ptr, length);

    uint16_t data_hdr_value = eieio_msg_ptr[0];
    void *event_pointer = (void *) &eieio_msg_ptr[1];

    if (data_hdr_value == 0) {

        // Count is 0, so no data
        return true;
    }

    log_debug("====================================");
    log_debug("eieio_msg_ptr: %08x", (uint32_t) eieio_msg_ptr);
    log_debug("event_pointer: %08x", (uint32_t) event_pointer);
    print_packet(eieio_msg_ptr);

    bool pkt_apply_prefix = (bool) (data_hdr_value >> 15);
    bool pkt_prefix_upper = (bool) ((data_hdr_value >> 14) & 0x1);
    bool pkt_payload_apply_prefix = (bool) (data_hdr_value >> 13 & 0x1);
    uint8_t pkt_type = (uint8_t) (data_hdr_value >> 10 & 0x3);
    uint8_t pkt_count = (uint8_t) (data_hdr_value & 0xFF);
    bool pkt_has_payload = (bool) (pkt_type & 0x1);

    uint32_t pkt_key_prefix = prefix;
    uint32_t pkt_payload_prefix = 0;
    bool pkt_payload_is_timestamp = (bool)((data_hdr_value >> 12) & 0x1);

    log_debug("data_hdr_value: %04x", data_hdr_value);
    log_debug("pkt_apply_prefix: %d", pkt_apply_prefix);
    log_debug("pkt_format: %d", pkt_prefix_upper);
    log_debug("pkt_payload_prefix: %d", pkt_payload_apply_prefix);
    log_debug("pkt_timestamp: %d", pkt_payload_is_timestamp);
    log_debug("pkt_type: %d", pkt_type);
    log_debug("pkt_count: %d", pkt_count);
    log_debug("payload_on: %d", pkt_has_payload);

    if (pkt_apply_prefix) {

        // Key prefix in the packet
        pkt_key_prefix = (uint32_t) event_pointer[0];
        event_pointer = (void*) (((uint16_t *) event_pointer) + 1);

        // If the prefix is in the upper part, shift the prefix
        if (pkt_prefix_upper) {
            pkt_key_prefix <<= 16;
        }
    } else if (!pkt_apply_prefix && apply_prefix) {

        // If there isn't a key prefix, but the config applies a prefix,
        // apply the prefix depending on the key_left_shift
        if (key_left_shift == 0) {
            pkt_prefix_upper = 1;
        } else {
            pkt_prefix_upper = 0;
        }
    }

    if (pkt_payload_apply_prefix) {
        if (!(pkt_type & 0x2)) {

            // If there is a payload prefix and the payload is 16-bit
            pkt_payload_prefix = (uint32_t) event_pointer[0];
            event_pointer = (void*) (((uint16_t *) event_pointer) + 1);
        } else {

            // If there is a payload prefix and the payload is 32-bit
            pkt_payload_prefix =
                (uint32_t) event_pointer[1] << 16 | event_pointer[0];
            event_pointer = (void*) (((uint16_t *) event_pointer) + 2);
        }
    }

    // If the packet has a payload that is a timestamp, but the timestamp
    // is not the current time, buffer it
    if (pkt_has_payload && pkt_payload_is_timestamp &&
            pkt_payload_prefix != time) {
        if (pkt_payload_prefix > time) {
            add_eieio_packet_to_sdram(eieio_msg_ptr);
            return true;
        }
        return false;
    }

    if (pkt_type <= 1) {
        process_16_bit_packets(
            event_pointer, pkt_prefix_upper, pkt_count, pkt_key_prefix,
            pkt_payload_prefix, pkt_has_payload, pkt_payload_is_timestamp);
        return true;
    } else {
        process_32_bit_packets(
            event_pointer, pkt_prefix_upper, pkt_count, pkt_key_prefix,
            pkt_payload_prefix, pkt_has_payload, pkt_payload_is_timestamp);
        return false;
    }
}

static inline void eieio_command_parse_stop_requests(
        eieio_msg_t eieio_msg_ptr, uint16_t length) {
    use(eieio_msg_ptr);
    use(length);
    log_debug("Stopping packet requests - parse_stop_packet_reqs");
    send_packet_reqs = false;
}

static inline void eieio_command_parse_start_requests(
        eieio_msg_t eieio_msg_ptr, uint16_t length) {
    use(eieio_msg_ptr);
    use(length);
    log_debug("Starting packet requests - parse_start_packet_reqs");
    send_packet_reqs = true;
}

static inline void eieio_command_parse_sequenced_data(
        eieio_msg_t eieio_msg_ptr, uint16_t length) {
    uint16_t sequence_value_region_id = eieio_msg_ptr[1];
    uint16_t region_id = sequence_value_region_id & 0xFF;
    uint16_t sequence_value = (sequence_value_region_id >> 8) & 0xFF;
    uint8_t next_expected_sequence_no =
        (pkt_last_sequence_seen + 1) & MAX_SEQUENCE_NO;
    eieio_msg_t eieio_content_pkt = &eieio_msg_ptr[2];

    if (region_id != BUFFER_REGION) {
        log_debug("received sequenced eieio packet with invalid region id:"
                  " %d.", region_id);
        signal_software_error(eieio_msg_ptr, length);
        incorrect_packets++;
    }

    log_debug("Received packet sequence number: %d", sequence_value);

    if (sequence_value != next_expected_sequence_no) {
        send_ack_last_state = true;
    } else {

        // parse_event_pkt returns false in case there is an error and the
        // packet is dropped (i.e. as it was never received)
        log_debug("add_eieio_packet_to_sdram");
        bool ret_value = add_eieio_packet_to_sdram(eieio_content_pkt,
                                                   length - 2);
        log_debug("add_eieio_packet_to_sdram return value: %d", ret_value);

        if (ret_value) {
            pkt_last_sequence_seen = next_expected_sequence_no;
        } else {
            log_debug("unable to buffer sequenced data packet.");
            signal_software_error(eieio_msg_ptr, length);
            incorrect_packets++;
        }
    }
}

static inline bool eieio_commmand_parse_packet(eieio_msg_t eieio_msg_ptr,
                                               uint16_t length) {
    uint16_t data_hdr_value = eieio_msg_ptr[0];
    uint16_t pkt_command = data_hdr_value & (~0xC000);

    switch (pkt_command) {
    case HOST_SEND_SEQUENCED_DATA:
        log_debug("command: HOST_SEND_SEQUENCED_DATA");
        eieio_command_parse_sequenced_data(eieio_msg_ptr, length);
        break;

    case STOP_SENDING_REQUESTS:
        log_debug("command: STOP_SENDING_REQUESTS");
        eieio_command_parse_stop_requests(eieio_msg_ptr, length);
        break;

    case START_SENDING_REQUESTS:
        log_debug("command: START_SENDING_REQUESTS");
        eieio_command_parse_start_requests(eieio_msg_ptr, length);
        break;

    case EVENT_STOP:
        log_debug("command: EVENT_STOP");
        time = simulation_ticks + 1;
        break;

    default:
        return false;
        break;
    }
    return true;
}

static inline bool packet_handler_selector(eieio_msg_t eieio_msg_ptr,
                                           uint16_t length) {
    log_debug("packet_handler_selector");

    uint16_t data_hdr_value = eieio_msg_ptr[0];
    uint8_t pkt_type = (data_hdr_value >> 14) && 0x03;

    if (pkt_type == 0x01) {
        log_debug("parsing a command packet");
        return eieio_commmand_parse_packet(eieio_msg_ptr, length);
    } else {
        log_debug("parsing an event packet");
        return eieio_data_parse_packet(eieio_msg_ptr, length);
    }
}

void fetch_and_process_packet() {
    log_debug("in fetch_and_process_packet");
    msg_from_sdram_in_use = false;

    // If we are not buffering, there is nothing to do
    if (buffer_region_size == 0) {
        return;
    }

    while ((!msg_from_sdram_in_use) && is_eieio_packet_in_buffer()) {

        // If there is padding, move on 2 bytes
        if (*read_pointer == 0x4002) {
            read_pointer += 2;
            if (read_pointer >= end_of_buffer_region) {
                read_pointer = buffer_region;
            }
        } else {
            uint8_t *src_ptr = (uint8_t *) read_pointer;
            uint8_t *dst_ptr = (uint8_t *) msg_from_sdram;
            uint32_t len = calculate_eieio_packet_size(
                (eieio_msg_t) read_pointer);
            uint32_t final_space = (end_of_buffer_region - read_pointer);

            log_debug("packet with length %d, from address: %08x", len,
                      read_pointer);

            if (len > final_space) {

                // If the packet is split, get the bits
                log_debug("split packet");
                log_debug("1 - reading packet to %08x from %08x length: %d",
                          (uint32_t) dst_ptr, (uint32_t) src_ptr, final_space);
                spin1_memcpy(dst_ptr, src_ptr, final_space);

                uint32_t remaining_len = len - final_space;
                dst_ptr += final_space;
                src_ptr = buffer_region;
                log_debug("2 - reading packet to %08x from %08x length: %d",
                          (uint32_t) dst_ptr, (uint32_t) src_ptr,
                          remaining_len);

                spin1_memcpy(dst_ptr, src_ptr, remaining_len);
                read_pointer = buffer_region + remaining_len;
            } else {

                // If the packet is whole, get the packet
                log_debug("full packet");
                log_debug("1 - reading packet to %08x from %08x length: %d",
                          (uint32_t) dst_ptr, (uint32_t) src_ptr, len);

                spin1_memcpy(dst_ptr, src_ptr, len);
                read_pointer += len;
                if (read_pointer >= end_of_buffer_region) {
                    read_pointer -= buffer_region_size;
                }
            }

            last_buffer_operation = BUFFER_OPERATION_READ;

            print_packet_bytes(msg_from_sdram, len);
            next_buffer_time = extract_time_from_eieio_msg(msg_from_sdram);
            log_debug("packet time: %d, current time: %d",
                      next_buffer_time, time);

            if (next_buffer_time == time) {
                packet_handler_selector(msg_from_sdram, len);
            } else {
                msg_from_sdram_in_use = true;
            }
        }
    }
}

void send_buffer_request_pkt(void) {
    uint32_t space = get_sdram_buffer_space_available();
    if (space >= space_before_data_request && space != last_space) {
        log_debug("sending request packet with space: %d and seq_no: %d",
                  space, pkt_last_sequence_seen);

        last_space = space;
        req_ptr->sequence |= pkt_last_sequence_seen;
        req_ptr->space_available = space;
        spin1_send_sdp_msg(&req, 1);
        req_ptr->sequence &= 0;
        req_ptr->space_available = 0;
    }
}

void timer_callback(uint unused0, uint unused1) {
    use(unused0);
    use(unused1);
    time++;

    log_debug("timer_callback, final time: %d, current time: %d,"
              "next packet buffer time: %d", simulation_ticks, time,
              next_buffer_time);

    if ((simulation_ticks != UINT32_MAX) && (time >= simulation_ticks + 1)) {
        log_info("Simulation complete.");
        log_info("Incorrect keys discarded: %d", incorrect_keys);
        log_info("Incorrect packets discarded: %d", incorrect_packets);
        spin1_exit(0);
        return;
    }

    if (send_packet_reqs || send_ack_last_state) {
        send_buffer_request_pkt();
    }

    if (!msg_from_sdram_in_use) {
        fetch_and_process_packet();
    } else if (next_buffer_time < time) {
        fetch_and_process_packet();
    } else if (next_buffer_time == time) {
        eieio_data_parse_packet(msg_from_sdram);
        fetch_and_process_packet();
    }
}

void sdp_packet_callback(uint mailbox, uint port) {
    use(port);
    sdp_msg_t *msg = (sdp_msg_t *) mailbox;
    uint16_t length = msg->length;
    eieio_msg_t eieio_msg_ptr = (eieio_msg_t) &(msg->cmd_rc);

    packet_handler_selector(eieio_msg_ptr, length - 8);

    // free the message to stop overload
    spin1_msg_free(msg);
}

bool setup_buffer_region(address_t, region_address) {
    buffer_region = (uint8_t *) region_address;
    read_pointer = buffer_region;
    write_pointer = buffer_region;
    return true;
}

bool read_parameters(address_t region_address) {

    // Get the configuration data
    apply_prefix = region_address[0];
    prefix = region_address[1];
    key_left_shift = region_address[2];
    check = region_address[3];
    key_space = region_address[4];
    mask = region_address[5];
    buffer_region_size = region_address[6];
    space_before_data_request = region_address[7];
    return_tag_id = region_address[8];

    // There is no point in sending requests until there is space for
    // at least one packet
    if (space_before_data_request < MIN_BUFFER_SPACE) {
        space_before_data_request = MIN_BUFFER_SPACE;
    }

    // Set the initial values
    incorrect_keys = 0;
    incorrect_packets = 0;
    msg_from_sdram_in_use = false;
    next_buffer_time = 0;
    pkt_last_sequence_seen = MAX_SEQUENCE_NO;
    end_of_buffer_region = buffer_region + buffer_region_size;
    send_ack_last_state = false;
    send_packet_reqs = true;

    if (buffer_region_size != 0) {
        last_buffer_operation = BUFFER_OPERATION_WRITE;
    } else {
        last_buffer_operation = BUFFER_OPERATION_READ;
    }

    // allocate a buffer size of the maximum SDP payload size
    msg_from_sdram = (eieio_msg_t) spin1_malloc(256);

    req.length = 8 + sizeof(req_packet_sdp_t);
    req.flags = 0x7;
    req.tag = return_tag_id;
    req.dest_port = 0xFF;
    req.srce_port = (1 << 5) | spin1_get_core_id();
    req.dest_addr = 0;
    req.srce_addr = spin1_get_chip_id();
    req_ptr = (req_packet_sdp_t*) &(req.cmd_rc);
    req_ptr->eieio_header_command = 1 << 14 | SPINNAKER_REQUEST_BUFFERS;
    req_ptr->chip_id = spin1_get_chip_id();
    req_ptr->processor = (spin1_get_core_id() << 3);
    req_ptr->pad1 = 0;
    req_ptr->region = BUFFER_REGION & 0x0F;

    log_info("apply_prefix: %d", apply_prefix);
    log_info("prefix: %d", prefix);
    log_info("key_left_shift: %d", key_left_shift);
    log_info("check: %d", check);
    log_info("key_space: 0x%08x", key_space);
    log_info("mask: 0x%08x", mask);
    log_info("buffer_region_size: %d", buffer_region_size);
    log_info("space_before_read_request: %d", space_before_data_request);
    log_info("return_tag_id: %d", return_tag_id);

    return true;
}

bool initialize(uint32_t *timer_period) {

    // Get the address this core's DTCM data starts at from SRAM
    address_t address = data_specification_get_data_address();

    // Read the header
    if (!data_specification_read_header(address)) {
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

    // Read the buffer region
    setup_buffer_region(region_start(BUFFER_REGION, address));

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

