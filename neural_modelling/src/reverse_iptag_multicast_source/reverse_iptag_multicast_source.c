#include "../common/common-impl.h"
#include <string.h>

#define EVENT_PADDING 2
#define EVENT_STOP 3
#define SEQUENCED_EIEIO_PKT 4
#define STOP_PACKET_REQUESTS 5
#define START_PACKET_REQUESTS 6

#define BUFFER_OPERATION_READ 0
#define BUFFER_OPERATION_WRITE 1

#define EIEIO_ACK_CMD 1
#define INITIAL_PACKET_FSM_STATE 0xFF

#pragma pack(1)

typedef uint16_t* eieio_msg_t;

typedef struct
{
  uint16_t event;
  uint16_t payload;
} event16_t;

typedef struct
{
  uint16_t eieio_header_command;
  uint16_t chip_id;
  uint16_t processor_command;
  uint16_t region_sequence;
  uint32_t space_available;
} req_packet_sdp_t;

// Declarations
bool multicast_source_data_filled(address_t base_address);
bool system_load_dtcm(void);
void timer_callback (uint unused0, uint unused1);
void sdp_packet_callback(uint mailbox, uint port);
void packet_handler_selector(eieio_msg_t eieio_msg_ptr);
bool parse_event_pkt(eieio_msg_t eieio_msg_ptr);
void parse_command_pkt(eieio_msg_t eieio_msg_ptr);
void parse_stop_packet_reqs(eieio_msg_t eieio_msg_ptr);
void parse_start_packet_reqs(eieio_msg_t eieio_msg_ptr);
void parse_sequenced_eieio_pkt(eieio_msg_t eieio_msg_ptr);
void send_buffer_request_pkt(void);
uint32_t check_sdram_buffer_space_available(void);
bool check_eieio_packets_available(void);
uint16_t calculate_eieio_packet_size(eieio_msg_t eieio_msg_ptr);
void fetch_and_process_packet(void);
bool add_eieio_packet_to_sdram(eieio_msg_t eieio_msg_ptr);
uint32_t extract_time_from_eieio_msg(eieio_msg_t eieio_msg_ptr);
void packet_interpreter(eieio_msg_t eieio_msg_ptr);
void process_16_bit_packets (void* event_pointer, bool pkt_format,
                            uint32_t length, uint32_t pkt_prefix,
                            uint32_t pkt_payload_prefix, bool payload,
                            bool pkt_payload_prefix_apply);
void process_32_bit_packets (void* event_pointer,
                            uint32_t length, uint32_t pkt_prefix,
                            uint32_t pkt_payload_prefix, bool payload,
                            bool pkt_payload_prefix_apply);

// Globals
static uint32_t time;
static bool apply_prefix;
static bool check;
static uint32_t prefix;
static uint32_t key_space;
static uint32_t mask;
static uint32_t incorrect_keys;
static uint32_t key_left_shift;

static uint32_t recording_info;
static uint32_t recording_region_size;
static uint32_t buffer_region_size;
static uint32_t size_of_buffer_to_read_in_bytes;

static uint8_t *buffer_region;
static uint8_t *end_of_buffer_region;
static uint8_t *write_pointer;
static uint8_t *read_pointer;

sdp_msg_t req;
req_packet_sdp_t *req_ptr;
static eieio_msg_t msg_from_sdram;
static bool msg_from_sdram_in_use;
static uint32_t next_buffer_time;
static uint8_t pkt_fsm;
static bool send_ack_last_state;
static bool send_packet_reqs;
static bool last_buffer_operation;
static uint8_t return_tag_id;



// Entry point
void c_main (void)
{
  // Configure system
  system_load_dtcm();

  // Set timer_callback
  spin1_set_timer_tick(timer_period);

  // Register callbacks
  spin1_callback_on (SDP_PACKET_RX, sdp_packet_callback, 0);
  spin1_callback_on (TIMER_TICK,    timer_callback,      0);

  log_info("Starting");

  // Start the time at "-1" so that the first tick will be 0
  time = UINT32_MAX;
  system_runs_to_completion();
}

//Data load functions
bool multicast_source_data_filled(address_t base_address)
{
  address_t region_address = region_start(1, base_address);

  read_pointer = write_pointer = buffer_region = (uint8_t *) region_start(2, base_address);

  // to write here retrieving the configuration of the population:
  // one 32 bit value which contains the three leftmost bits
  // Prefix, Format and Prefix Check
  // The lowest 16 bits are the prefix itself

  apply_prefix = region_address[0];
  prefix = region_address[1];
  key_left_shift = region_address[2];
  check = region_address[3];
  key_space = region_address[4];
  mask = region_address[5];
  recording_info = region_address[6];
  recording_region_size = region_address[7];
  buffer_region_size = region_address[8];
  size_of_buffer_to_read_in_bytes = region_address[9];
  return_tag_id = region_address[10];

  incorrect_keys = 0;
  msg_from_sdram_in_use = 0;
  next_buffer_time = 0;
  pkt_fsm = INITIAL_PACKET_FSM_STATE;
  end_of_buffer_region = buffer_region + buffer_region_size;
  send_ack_last_state = 0;
  send_packet_reqs = 1;

  if (buffer_region_size != 0)
    last_buffer_operation = BUFFER_OPERATION_WRITE;
  else
    last_buffer_operation = BUFFER_OPERATION_READ;

  //allocate a buffer size of the maximum SDP payload size
  msg_from_sdram = (eieio_msg_t) spin1_malloc(256);

  req.length = 10 + sizeof(req_packet_sdp_t);
  req.flags = 0x7;
  req.tag = return_tag_id;
  req.dest_port = 0xFF;
  req.srce_port = (1 << 5) | spin1_get_core_id();
  req.dest_addr = 0;
  req.srce_addr = spin1_get_chip_id();
  req_ptr = (req_packet_sdp_t*) &(req.cmd_rc);
  req_ptr -> eieio_header_command = 1 << 14 | EIEIO_ACK_CMD;
  req_ptr -> chip_id = spin1_get_chip_id();
  req_ptr -> processor_command = (spin1_get_core_id() << 11) | (1 << 7);
  req_ptr -> region_sequence = (1 << 8);


  io_printf (IO_BUF, "apply_prefix: %d\n", apply_prefix);
  io_printf (IO_BUF, "prefix: %d\n", prefix);
  io_printf (IO_BUF, "key_left_shift: %d\n", key_left_shift);
  io_printf (IO_BUF, "check: %d\n", check);
  io_printf (IO_BUF, "key_space: 0x%08x\n", key_space);
  io_printf (IO_BUF, "mask: 0x%08x\n", mask);
  io_printf (IO_BUF, "recording_info: 0x%08x\n", recording_info);
  io_printf (IO_BUF, "recording_region_size: %d\n", recording_region_size);
  io_printf (IO_BUF, "buffer_region_size: %d\n", buffer_region_size);
  io_printf (IO_BUF, "size_of_buffer_to_read_in_bytes: %d\n", size_of_buffer_to_read_in_bytes);
  io_printf (IO_BUF, "return_tag_id: %d\n", return_tag_id);


  return (true);
}

bool system_load_dtcm(void)
{
  // Get the address this core's DTCM data starts at from SRAM
  address_t address = system_load_sram();

  uint32_t version;
  uint32_t flags = 0;
  if(!system_header_filled (address, &version, flags))
    return (false);

  system_load_params(region_start(0, address));

  if (!multicast_source_data_filled(address))
    return (false);

  return (true);
}

// Callbacks
void timer_callback (uint unused0, uint unused1)
{
  use(unused0);
  use(unused1);
  time++;

  if ((simulation_ticks != UINT32_MAX) 
    && (time >= simulation_ticks + timer_period))
  {
    log_info("Simulation complete.");
    log_info("Incorrect keys discarded: %d", incorrect_keys);
    spin1_exit(0);
    return;
  }

  if (send_packet_reqs || send_ack_last_state)
    send_buffer_request_pkt();

  if (!msg_from_sdram_in_use)
    fetch_and_process_packet();
  else if (msg_from_sdram_in_use && next_buffer_time < time)
  {
    msg_from_sdram_in_use = 0;
    fetch_and_process_packet();
  }
  else if (msg_from_sdram_in_use && next_buffer_time == time)
  {
    packet_interpreter(msg_from_sdram);
    msg_from_sdram_in_use = 0;
    fetch_and_process_packet();
  }
}

void sdp_packet_callback(uint mailbox, uint port)
{
  use(port);
  sdp_msg_t *msg = (sdp_msg_t *) mailbox;

  eieio_msg_t eieio_msg_ptr = (eieio_msg_t) &(msg -> cmd_rc);

  packet_handler_selector(eieio_msg_ptr);

  //free the message to stop overload
  spin1_msg_free(msg);
}

void packet_handler_selector(eieio_msg_t eieio_msg_ptr)
{
  uint16_t data_hdr_value = eieio_msg_ptr[0];
  bool pkt_apply_prefix = (bool) (data_hdr_value >> 15);
  bool pkt_mode = data_hdr_value >> 14;

  if (pkt_apply_prefix == 0 && pkt_mode == 1)
    parse_command_pkt(eieio_msg_ptr);
  else
    parse_event_pkt(eieio_msg_ptr);
}

//Utility functions
uint32_t check_sdram_buffer_space_available(void)
{
  uint32_t buffer_region_value = (uint32_t) buffer_region;
  uint32_t write_ptr_value = (uint32_t) write_pointer;
  uint32_t read_ptr_value = (uint32_t) read_pointer;
  uint32_t end_of_buffer_region_value = (uint32_t) end_of_buffer_region;
  uint32_t return_value = 0;

  io_printf (IO_BUF, "       buffer_region: 0x%08x\n", buffer_region_value);
  io_printf (IO_BUF, "           write_ptr: 0x%08x\n", write_ptr_value);
  io_printf (IO_BUF, "            read_ptr: 0x%08x\n", read_ptr_value);
  io_printf (IO_BUF, "end_of_buffer_region: 0x%08x\n", end_of_buffer_region_value);

  if (read_ptr_value < write_ptr_value)
  {
    uint32_t final_space = end_of_buffer_region_value - write_ptr_value;
    uint32_t initial_space = read_ptr_value - buffer_region_value;

    if (final_space < 10 && initial_space < 10)
      return_value = 0;
    else if (final_space < 10 && initial_space >= 10)
      return_value = initial_space;
    else if (final_space >= 10)
      return_value = final_space;
  }
  else if (write_ptr_value < read_ptr_value)
  {
    uint32_t middle_space = read_ptr_value - write_ptr_value;

    if (middle_space < 10)
      return_value = 0;
    else
      return_value = middle_space;
  }
  else
    if (last_buffer_operation == BUFFER_OPERATION_WRITE)
      return_value = 0;
    else
      return_value = buffer_region_size;

  io_printf (IO_BUF, "return value: %d\n", return_value);
}

bool check_eieio_packets_available(void)
{
  uint32_t write_ptr_value = (uint32_t) write_pointer;
  uint32_t read_ptr_value = (uint32_t) read_pointer;

  if (buffer_region_size == 0)
    return 0;

  if (write_ptr_value != read_ptr_value)
    return 1;
  else if (last_buffer_operation == BUFFER_OPERATION_WRITE)
    return 1;
  else
    return 0;
}

void parse_command_pkt(eieio_msg_t eieio_msg_ptr)
{
  uint16_t data_hdr_value = eieio_msg_ptr[0];
  uint16_t pkt_command = data_hdr_value & (~0xC000);

  switch (pkt_command)
  {
    case SEQUENCED_EIEIO_PKT:
      parse_sequenced_eieio_pkt(eieio_msg_ptr);
      break;
    case STOP_PACKET_REQUESTS:
      parse_stop_packet_reqs(eieio_msg_ptr);
      break;
    case START_PACKET_REQUESTS:
      parse_start_packet_reqs(eieio_msg_ptr);
      break;
    default:
      break;
  }
}

void parse_stop_packet_reqs(eieio_msg_t eieio_msg_ptr)
{
  use(eieio_msg_ptr);
  send_packet_reqs = 0;
}

void parse_start_packet_reqs(eieio_msg_t eieio_msg_ptr)
{
  use(eieio_msg_ptr);
  send_packet_reqs = 1;
}

void parse_sequenced_eieio_pkt(eieio_msg_t eieio_msg_ptr)
{
  uint16_t sequence_value = eieio_msg_ptr[1];
  uint8_t next_state_fsm = (pkt_fsm + 1) & 0xFF;
  eieio_msg_t eieio_event_pkt = &eieio_msg_ptr[2];

  if (sequence_value != next_state_fsm)
    send_ack_last_state = 1;
  else
  {
    //parse_event_pkt returns false in case there is an error and the packet
    //is dropped (i.e. as it was never received)
    if (parse_event_pkt(eieio_event_pkt))
      pkt_fsm = next_state_fsm;
  }
}

void send_buffer_request_pkt(void)
{
  req_ptr -> region_sequence |= pkt_fsm;
  req_ptr -> space_available = check_sdram_buffer_space_available();
  spin1_send_sdp_msg (&req, 1);
  req_ptr -> region_sequence &= 0xFF00;
  req_ptr -> space_available = 0;
}

uint16_t calculate_eieio_packet_size(eieio_msg_t eieio_msg_ptr)
{
  uint16_t data_hdr_value = eieio_msg_ptr[0];
  uint8_t pkt_type = (uint8_t) (data_hdr_value >> 10 & 0x3);
  bool pkt_apply_prefix = (bool) (data_hdr_value >> 15);
  bool pkt_payload_prefix_apply = (bool) (data_hdr_value >> 13 & 0x1);
  uint8_t event_count = data_hdr_value & 0xFF;
  uint16_t event_size, total_size;
  uint16_t header_size = 2;

  switch(pkt_type)
  {
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
  }

  if (pkt_apply_prefix)
    header_size += 2;
  if (pkt_payload_prefix_apply)
  {
    if(pkt_type == 0 || pkt_type == 1)
      header_size += 2;
    else
      header_size += 4;
  }

  total_size = event_count * event_size + header_size;
  return total_size;
}

bool parse_event_pkt(eieio_msg_t eieio_msg_ptr)
{
  uint16_t data_hdr_value = eieio_msg_ptr[0];
  bool pkt_timestamp = (bool) (data_hdr_value >> 12 & 0x1);

  if (!pkt_timestamp || time == extract_time_from_eieio_msg(eieio_msg_ptr))
  {
    packet_interpreter(eieio_msg_ptr);
    return 1;
  }
  else
    return add_eieio_packet_to_sdram(eieio_msg_ptr);
}

void fetch_and_process_packet(void)
{
  io_printf (IO_BUF, "in fetch_and_process_packet\n");
  if (buffer_region_size == 0)
  {
    msg_from_sdram_in_use = 0;
    return;
  }

  uint16_t *padding_checker = (uint16_t *) read_pointer;
  io_printf (IO_BUF, "padding_checker: %d\n", *padding_checker);

  while (
    (!msg_from_sdram_in_use) && 
    check_eieio_packets_available() &&
    !(read_pointer == buffer_region && *padding_checker == 0))
  {
    padding_checker = (uint16_t *) read_pointer;
    io_printf (IO_BUF, "padding_checker: %d\n", *padding_checker);

    if (*padding_checker == 0)
      read_pointer = buffer_region;

    void *src_ptr = (void *) read_pointer;
    void *dst_ptr = (void *) msg_from_sdram;
    uint32_t len = calculate_eieio_packet_size((eieio_msg_t) read_pointer);

    spin1_memcpy (dst_ptr, src_ptr, len);
    last_buffer_operation = BUFFER_OPERATION_READ;
    msg_from_sdram_in_use = 1;
    read_pointer += len;
    if (read_pointer >= end_of_buffer_region)
      read_pointer -= buffer_region_size;

    next_buffer_time = extract_time_from_eieio_msg(msg_from_sdram);
    io_printf (IO_BUF, "packet time: %d\n", next_buffer_time);
    io_printf (IO_BUF, "current time: %d\n", time);
    if (next_buffer_time == time)
    {
      packet_handler_selector(msg_from_sdram);
      msg_from_sdram_in_use = 0;
    }
    io_printf (IO_BUF, "loop completed\n");
  }
}

bool add_eieio_packet_to_sdram(eieio_msg_t eieio_msg_ptr)
{
  uint32_t len = calculate_eieio_packet_size(eieio_msg_ptr);
  uint32_t buffer_region_value = (uint32_t) buffer_region;
  uint32_t write_ptr_value = (uint32_t) write_pointer;
  uint32_t read_ptr_value = (uint32_t) read_pointer;
  uint32_t end_of_buffer_region_value = (uint32_t) end_of_buffer_region;

  if (read_ptr_value < write_ptr_value)
  {
    uint32_t final_space = end_of_buffer_region_value - write_ptr_value;
    uint32_t initial_space = read_ptr_value - buffer_region_value;

    if (final_space < len && initial_space < len)
      return 0;
    else if (final_space < len && initial_space >= len)
    {
      //add final padding
      for (; write_pointer < end_of_buffer_region; write_pointer++)
        *write_pointer = 0;

      //add packet at the beginning
      write_pointer = buffer_region;
      spin1_memcpy(write_pointer, eieio_msg_ptr, len);
      write_pointer += len;
      last_buffer_operation = BUFFER_OPERATION_WRITE;
      return 1;
    }
    else if (final_space >= len)
    {
      //add packet at the end
      spin1_memcpy(write_pointer, eieio_msg_ptr, len);
      write_pointer += len;
      last_buffer_operation = BUFFER_OPERATION_WRITE;
      if (write_pointer == end_of_buffer_region)
        write_pointer = buffer_region;
      return 1;
    }
  }
  else if (write_ptr_value < read_ptr_value)
  {
    uint32_t middle_space = read_ptr_value - write_ptr_value;

    if (middle_space < len)
      return 0;
    else
    {
      //add packet in the middle space
      spin1_memcpy(write_pointer, eieio_msg_ptr, len);
      write_pointer += len;
      last_buffer_operation = BUFFER_OPERATION_WRITE;
      if (write_pointer == end_of_buffer_region)
        write_pointer = buffer_region;
      return 1;
    }
  }
  else
  // the two pointers may be equal, indicating that either the list
  // is full or it is empty, depending on the last operation
  {
    if (last_buffer_operation == BUFFER_OPERATION_WRITE)
      return 0;
    else
    {
      //add packet in the space available
      spin1_memcpy(write_pointer, eieio_msg_ptr, len);
      write_pointer += len;
      last_buffer_operation = BUFFER_OPERATION_WRITE;
      if (write_pointer == end_of_buffer_region)
        write_pointer = buffer_region;
      return 1;
    }
  }
}

uint32_t extract_time_from_eieio_msg(eieio_msg_t eieio_msg_ptr)
{
  uint16_t data_hdr_value = eieio_msg_ptr[0];
  bool pkt_timestamp = (bool) (data_hdr_value >> 12 & 0x1);
  bool pkt_apply_prefix = (bool) (data_hdr_value >> 15);
  bool pkt_mode = data_hdr_value >> 14;

  if (pkt_apply_prefix == 0 && pkt_mode == 1)
    return time;

  if (pkt_timestamp)
  {
    bool pkt_payload_prefix_apply = (bool) (data_hdr_value >> 13 & 0x1);
    uint8_t pkt_type = (uint8_t) (data_hdr_value >> 10 & 0x3);
    bool pkt_apply_prefix = (bool) (data_hdr_value >> 15);
    uint32_t payload_prefix_time = 0;
    uint32_t payload_time = 0;
    uint16_t *payload_prefix;
    uint16_t *event_ptr;

    if (pkt_apply_prefix)
      payload_prefix = &eieio_msg_ptr[2];
    else
      payload_prefix = &eieio_msg_ptr[1];

    if (pkt_type & 0x2) // 32 bit packet
      event_ptr = &payload_prefix[2];
    else
      event_ptr = &payload_prefix[1];

    if (pkt_payload_prefix_apply)
      if (pkt_type & 0x2) // 32 bit packet
        payload_prefix_time = payload_prefix[1] << 16 | payload_prefix[0];
      else // 16 bit packet
        payload_prefix_time = payload_prefix[0];
    else if (pkt_type & 0x1)
      if (pkt_type & 0x2) // 32 bit packet
        payload_time = event_ptr[3] << 16 | event_ptr[2];
      else // 16 bit packet
        payload_time = event_ptr[1];
    else
      return 0;

    return payload_prefix_time | payload_time;
  }
  else
    return 0;
}

void packet_interpreter(eieio_msg_t eieio_msg_ptr)
{
  io_printf (IO_BUF, "packet_interpreter\n");
  uint16_t data_hdr_value = eieio_msg_ptr[0];
  void *event_pointer = (void *) &eieio_msg_ptr[1];

  if (data_hdr_value == 0) //data retrieved is padding
    return;

#ifdef DEBUG
  log_info("\n");
  log_info("====================================");
  log_info("eieio_msg_ptr: %08x", (uint32_t) eieio_msg_ptr);
  log_info("event_pointer: %08x", (uint32_t) event_pointer);

  uint32_t len = calculate_eieio_packet_size(eieio_msg_ptr);
  uint8_t *ptr = (uint8_t *) eieio_msg_ptr;

  log_info("packet lenght: %d", len);
  for (uint32_t i = 0; i < len; i++)
    io_printf(IO_BUF, "%02x ", ptr[i]);
  io_printf(IO_BUF, "\n");
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

//#ifdef DEBUG
  io_printf (IO_BUF, "data_hdr_value: %04x\n", data_hdr_value);
  io_printf (IO_BUF, "pkt_apply_prefix: %d\n", pkt_apply_prefix);
  io_printf (IO_BUF, "pkt_format: %d\n", pkt_format);
  io_printf (IO_BUF, "pkt_payload_prefix: %d\n", pkt_payload_prefix_apply);
  io_printf (IO_BUF, "pkt_timestamp: %d\n", pkt_timestamp);
  io_printf (IO_BUF, "pkt_type: %d\n", pkt_type);
  io_printf (IO_BUF, "pkt_len: %d\n", pkt_len);
  io_printf (IO_BUF, "payload_on: %d\n", payload_on);
//#endif

  if (extract_time_from_eieio_msg(eieio_msg_ptr) != time)
    return;

  if (pkt_apply_prefix)
  {
    uint16_t *key_prefix_ptr = (uint16_t *) event_pointer;
    event_pointer = (void*) (((uint16_t *) event_pointer) + 1);

    pkt_key_prefix = (uint32_t) key_prefix_ptr[0];

    if (pkt_format) pkt_key_prefix <<= 16;
  }
  else if (!pkt_apply_prefix && apply_prefix)
  {
    if (key_left_shift == 0)
      pkt_format = 1;
    else
      pkt_format = 0;
  }

  if (pkt_payload_prefix_apply)
  {
    if (!(pkt_type & 0x2)) //16 bit type packet
    {
      uint16_t *payload_prefix_ptr = (uint16_t *) event_pointer;
      event_pointer = (void*) (((uint16_t *) event_pointer) + 1);

      pkt_payload_prefix = (uint32_t) payload_prefix_ptr[0];
    }
    else //32 bit type packet
    {
      uint16_t *payload_prefix_ptr = (uint16_t *) event_pointer;
      event_pointer = (void*) (((uint16_t *) event_pointer) + 2);

      uint32_t temp1 = payload_prefix_ptr[0];
      uint32_t temp2 = payload_prefix_ptr[1];
      pkt_payload_prefix = temp2 << 16 | temp1;
    }
  }

  if (pkt_type <= 1)
    process_16_bit_packets (event_pointer, pkt_format, pkt_len, pkt_key_prefix,
                            pkt_payload_prefix, payload_on,
                            pkt_payload_prefix_apply);
  else
    process_32_bit_packets (event_pointer, pkt_len, pkt_key_prefix,
                            pkt_payload_prefix, payload_on,
                            pkt_payload_prefix_apply);
}

void process_16_bit_packets (void* event_pointer, bool pkt_format,
                            uint32_t length, uint32_t pkt_prefix,
                            uint32_t pkt_payload_prefix, bool payload,
                            bool pkt_payload_prefix_apply)
{
  uint32_t i;

#ifdef DEBUG
  log_info("process_16_bit_packets");
  log_info("event_pointer: %08x", (uint32_t) event_pointer);
  log_info("length: %d", length);
  log_info("pkt_prefix: %08x", pkt_prefix);
  log_info("pkt_payload_prefix: %08x", pkt_payload_prefix);
  log_info("payload on: %d", payload);
  log_info("pkt_format: %d", pkt_format);
#endif

  if (!payload && !pkt_payload_prefix_apply)
  {
    uint16_t *events_array = (uint16_t *) event_pointer;

#ifdef DEBUG
    log_info("16 bit, no payload");
#endif

    for (i = 0; i < length; i++)
    {
      uint32_t key = (uint32_t) (events_array[i]);

      if (!pkt_format) key <<= 16;
      key |= pkt_prefix;

#ifdef DEBUG
      log_info("mc packet 16 key: %08x", key);
      log_info("check before send packet: %d", 
                (!check) || (check && ((key & mask) == key_space)));
#endif

      if ( (!check) || (check && ((key & mask) == key_space)))
        spin1_send_mc_packet(key, NULL, NO_PAYLOAD);
      else
        incorrect_keys++;
    }
  }
  else if (!payload && pkt_payload_prefix_apply)
  {
    uint16_t *events_array = (uint16_t *) event_pointer;
    uint32_t payload = pkt_payload_prefix;

#ifdef DEBUG
    log_info("16 bit, fixed payload");
#endif

    for (i = 0; i < length; i++)
    {
      uint32_t key = (uint32_t) (events_array[i]);

      if (!pkt_format) key <<= 16;
      key |= pkt_prefix;

#ifdef DEBUG
      log_info("mc packet 16 key: %08x, payload: %08x", key, payload);
      log_info("check before send packet: %d", 
                (!check) || (check && ((key & mask) == key_space)));
#endif

      if ( (!check) || (check && ((key & mask) == key_space)))
        spin1_send_mc_packet(key, payload, WITH_PAYLOAD);
      else
        incorrect_keys++;
    }
  }
  else
  {
    event16_t *events_struct = (event16_t *) event_pointer;

#ifdef DEBUG
    log_info("16 bit, with payload");
#endif

    for (i = 0; i < length; i++)
    {
      uint32_t payload = (uint32_t) events_struct[i].payload;
      uint32_t key = (uint32_t) events_struct[i].event;

      if (!pkt_format) key <<= 16;
      key |= pkt_prefix;
      payload |= pkt_payload_prefix;

#ifdef DEBUG
      log_info("mc packet 16 key: %08x, payload: %08x", key, payload);
      log_info("check before send packet: %d", 
                (!check) || (check && ((key & mask) == key_space)));
#endif

      if ( (!check) || (check && ((key & mask) == key_space)))
        spin1_send_mc_packet(key, payload, WITH_PAYLOAD);
      else
        incorrect_keys++;
    }
  }
}

void process_32_bit_packets (void* event_pointer,
                            uint32_t length, uint32_t pkt_prefix,
                            uint32_t pkt_payload_prefix, bool payload,
                            bool pkt_payload_prefix_apply)
{
  uint32_t i;

#ifdef DEBUG
  log_info("process_32_bit_packets");
  log_info("event_pointer: %08x", (uint32_t) event_pointer);
  log_info("length: %d", length);
  log_info("pkt_prefix: %08x", pkt_prefix);
  log_info("pkt_payload_prefix: %08x", pkt_payload_prefix);
  log_info("payload: %d", payload);
  log_info("pkt_payload_prefix_apply: %d", pkt_payload_prefix_apply);
#endif

  if (!payload && !pkt_payload_prefix_apply)
  {
    uint16_t *events = (uint16_t *) event_pointer;

#ifdef DEBUG
    log_info("32 bit, no payload");
#endif

    for (i = 0; i < (length << 1); i+=2)
    {
      uint32_t key;
      uint32_t temp1 = events[i];
      uint32_t temp2 = events[i+1];

      key = temp2 << 16 | temp1;
      key |= pkt_prefix;

#ifdef DEBUG
      log_info("mc packet 32 key: %08x", key);
      log_info("check before send packet: %d", 
              (!check) || (check && ((key & mask) == key_space)));
#endif

      if ( (!check) || (check && ((key & mask) == key_space)))
        spin1_send_mc_packet(key, NULL, NO_PAYLOAD);
      else
        incorrect_keys++;
    }
  }
  else if (!payload && pkt_payload_prefix_apply)
  {
    uint16_t *events = (uint16_t *) event_pointer;
    uint32_t payload = pkt_payload_prefix;

#ifdef DEBUG
    log_info("32 bit, fixed payload");
#endif

    for (i = 0; i < (length << 1); i+=2)
    {
      uint32_t key;
      uint32_t temp1 = events[i];
      uint32_t temp2 = events[i+1];

      key = temp2 << 16 | temp1;
      key |= pkt_prefix;

#ifdef DEBUG
      log_info("mc packet 32 key: %08x, payload: %08x", key, payload);
      log_info("check before send packet: %d", 
                (!check) || (check && ((key & mask) == key_space)));
#endif

      if ( (!check) || (check && ((key & mask) == key_space)))
        spin1_send_mc_packet(key, payload, WITH_PAYLOAD);
      else
        incorrect_keys++;
    }
  }
  else
  {
    uint16_t *events = (uint16_t *) event_pointer;

#ifdef DEBUG
    log_info("32 bit, with payload");
#endif

    for (i = 0; i < (length << 2); i+=4)
    {
      uint32_t key;
      uint32_t payload;

      uint32_t temp1 = events[i];
      uint32_t temp2 = events[i+1];
      key = temp2 << 16 | temp1;
      key |= pkt_prefix;

      temp1 = events[i+2];
      temp2 = events[i+3];
      payload = temp2 << 16 | temp1;
      payload |= pkt_payload_prefix;

#ifdef DEBUG
      log_info("mc packet 32 key: %08x, payload: %08x", key, payload);
      log_info("check before send packet: %d", 
              (!check) || (check && ((key & mask) == key_space)));
#endif

      if ( (!check) || (check && ((key & mask) == key_space)))
        spin1_send_mc_packet(key, payload, WITH_PAYLOAD);
      else
        incorrect_keys++;
    }
  }
}
