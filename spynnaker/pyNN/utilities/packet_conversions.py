__author__ = 'stokesa6'

#define key_x(k) (k >> 24)
#define key_y(k) ((k >> 16) & 0xFF)
#define key_p(k) ((k >> 11) & 0xF)
#define nid(k) (k & 0x8FF)

# basic key to coordinates converters


def get_x_from_key(key):
    return key >> 24


def get_y_from_key(key):
    return (key >> 16) & 0xFF


def get_p_from_key(key):
    return (key >> 11) & 0x1F
    #modified by ABS to reflect the fact that there are 5 bits for p


def get_nid_from_key(key):
    return key & 0x7FF


def get_key_from_coords(chipX, chipY, chipP):
    return chipX << 24 | chipY << 16 | chipP << 11


def get_mpt_sb_mem_addrs_from_coords(x, y, p):  #used to
    return (p + (18 * y) + (18 * 8 * x)) * 2  #two bytes per entry


# robot with 7 7 1
def get_x_from_robot_retina(key):
    return (key >> 7) & 0x7f
    #return (key >> 8) & 0x7f


def get_y_from_robot_retina(key):
    return key & 0x7f


def get_spike_value_from_robot_retina(key):
    return (key >> 14) & 0x1


# fpga conversion
def get_y_from_fpga_retina(key, mode):
    if mode == 128:
        return key & 0x7f
    elif mode == 64:
        return key & 0x3f
    elif mode == 32:
        return key & 0x1f
    elif mode == 16:
        return key & 0xf
    else:
        return None


def get_x_from_fpga_retina(key, mode):
    if mode == 128:
        return (key >> 7) & 0x7f
    elif mode == 64:
        return (key >> 6) & 0x3f
    elif mode == 32:
        return (key >> 5) & 0x1f
    elif mode == 16:
        return (key >> 4) & 0xf
    else:
        return None


def get_spike_value_from_fpga_retina(key, mode):
    if mode == 128:
        return (key >> 14) & 0x1
    elif mode == 64:
        return (key >> 14) & 0x1
    elif mode == 32:
        return (key >> 14) & 0x1
    elif mode == 16:
        return (key >> 14) & 0x1
    else:
        return None



