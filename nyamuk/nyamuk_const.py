'''
MQTT Constants
@author Iwan Budi Kusnanto
'''
UNKNOWN_VAL = -1

#
# version specifics settings
specs = {
    3: {
        'name': 'MQIsdp',
        'hdrsize': 12,
    },
    4: {
        'name': 'MQTT',
        'hdrsize': 12,
    },
    5: {
        'name': 'MQTT',
        # note: properties length is a var size (1 to 4) so dynamically computed
        'hdrsize': 10,
    },
}


#CLIENT_STATE
CS_NEW = 0
CS_CONNECTED = 1
CS_DISCONNECTING = 2

#socket
INVALID_SOCKET = -1

#keep alive timer, in seconds
KEEPALIVE_VAL = 120

#ERROR
ERR_SUCCESS = 0
ERR_NO_MEM = 1
ERR_PROTOCOL = 2
ERR_INVAL = 3
ERR_NO_CONN = 4
ERR_CONN_REFUSED = 5
ERR_NOT_FOUND = 6
ERR_CONN_LOST = 7
ERR_SSL = 8
ERR_PAYLOAD_SIZE = 9
ERR_NOT_SUPPORTED = 10
ERR_AUTH = 11
ERR_ACL_DENIED = 12
ERR_UNKNOWN = 13

#COMMAND
CMD_CONNECT = 0x10
CMD_CONNACK = 0x20
CMD_PUBLISH = 0x30
CMD_PUBACK = 0x40
CMD_PUBREC = 0x50
CMD_PUBREL = 0x60
CMD_PUBCOMP = 0x70
CMD_SUBSCRIBE = 0x80
CMD_SUBACK = 0x90
CMD_UNSUBSCRIBE = 0xA0
CMD_UNSUBACK = 0xB0
CMD_PINGREQ = 0xC0
CMD_PINGRESP = 0xD0
CMD_DISCONNECT = 0xE0
CMD_AUTH = 0xF0

#OTHER
MESSAGE_RETRY = 20

#DIRECTION
DIRECTION_NONE = -1
DIRECTION_IN = 0
DIRECTION_OUT = 1

#MESSAGE STATE
MS_INVALID = 0
MS_WAIT_PUBACK = 1
MS_WAIT_PUBREC = 2
MS_WAIT_PUBREL = 3
MS_WAIT_PUBCOMP = 4

#CONNECT RETURN CODE
CONNECT_ACCEPTED = 0
CONNECT_RFSD_PROTO = 1
CONNECT_RFSD_ID = 2
CONNECT_RFSD_SERVER_UNAVAIL = 3
CONNECT_RFSD_BAD_USERPASS = 4
CONNECT_RFSD_NOT_AUTH = 5

# PROPERTIES (MQTT 5)
PROP_PAYLOAD_FORMAT_INDICATOR  = 0x01
PROP_MSG_EXPIRY_INTERVAL       = 0x02
PROP_CONTENT_TYPE              = 0x03
PROP_RESP_TOPIC                = 0x08
PROP_CORRELATION_DATA          = 0x09
PROP_SUBSCR_ID                 = 0x0B
PROP_SESS_EXPIRY_INTERVAL      = 0x11
PROP_ASSIGNED_CLIENT_ID        = 0x12
PROP_SRV_KEEPALIVE             = 0x13
PROP_AUTH_METHOD               = 0x15
PROP_AUTH_DATA                 = 0x16
PROP_REQUEST_PROBLEM_NFO       = 0x17
PROP_WILL_DELAY_INTERVAL       = 0x18
PROP_REQ_RESP_NFO              = 0x19
PROP_RESP_NFO                  = 0x1A
PROP_SRV_REF                   = 0x1C
PROP_REASON_STRING             = 0x1F
PROP_RECV_MAX                  = 0x21
PROP_TOPIC_ALIAS_MAX           = 0x22
PROP_TOPIC_ALIAS               = 0x23
PROP_MAX_QOS                   = 0x24
PROP_RETAIN_AVAILABLE          = 0x25
PROP_USR_PROPERTY              = 0x26
PROP_MAX_PKT_SIZE              = 0x27
PROP_WILDCARD_SUBSCR_AVAILABLE = 0x28
PROP_SUBSCR_ID_AVAILABLE       = 0x29
PROP_SHARED_SUBSCR_AVAILABLE   = 0x2A

def len_bytes(val):
    """
        val: bytearray
    """
    return 2 + len(val)

def len_var_bytes_int(val):
    """
        val: (possibly large) integer

        0 - 127   : 1 byte
        128 - 2^14: 2 bytes
        ...
    """
    if val == 0:
        return 1

    count = 0
    while val > 0:
        val   /= 128
        count += 1

    if count > 4:
        raise Exception("up to 4 bytes")

    return count

def len_string(val):
    """
        val: utf-8 string
    """
    return 2 + len(val)

def len_string_pair((key, value)):
    return 4 + len(key) + len(value)


DATATYPE_BYTE         = 0x01
DATATYPE_UINT16       = 0x02
DATATYPE_UINT32       = 0x03
DATATYPE_VAR_BYTE_INT = 0x04
DATATYPE_BYTES        = 0x05
DATATYPE_UTF8         = 0x06
DATATYPE_UTF8_PAIR    = 0x07

DATATYPE_LEN = {
    DATATYPE_BYTE        : 1,
    DATATYPE_UINT16      : 2,
    DATATYPE_UINT32      : 4,
    DATATYPE_VAR_BYTE_INT: len_var_bytes_int,
    DATATYPE_BYTES       : len_bytes,
    DATATYPE_UTF8        : len_string,
    DATATYPE_UTF8_PAIR   : len_string_pair,
}

PROPS_NAME = {
    0x01: "PAYLOAD FORMAT INDICATOR",
    0x02: "MESSAGE EXPIRY INTERVAL",
    0x03: "CONTENT TYPE",
    0x08: "RESPONSE TOPIC",
    0x09: "CORRELATION DATA",
    0x0B: "SUBSCRIPTION ID",
    0x11: "SESSION_EXPIRY_INTERVAL",
    0x12: "ASSIGNED CLIENT ID",
    0x13: "SERVER KEEPALIVE",
    0x15: "AUTH METHOD",
    0x16: "AUTH DATA",
    0x17: "REQUEST PROBLEM INFO",
    0x18: "WILL DELAY INTERVAL",
    0x19: "REQUEST RESPONSE INFO",
    0x1A: "RESPONSE INFO",
    0x1C: "SERVER REFERENCE",
    0x1F: "REASON STRING",
    0x21: "RECEIVE MAXIMUM",
    0x22: "TOPIC ALIAS MAXIMUM",
    0x23: "TOPIC ALIAS",
    0x24: "MAXIMUM QOS",
    0x25: "RETAIN AVAILABLE",
    0x26: "USER PROPERTY",
    0x27: "MAX PACKET SIZE",
    0x28: "WILDCARD SUBCRIPTION AVAILABLE",
    0x29: "SUBSCRIPTION ID AVAILABLE",
    0x2A: "SHARE SUBSCRIPTION AVAILABLE",
}

PROPS_DATA_TYPE = {
    0x01: DATATYPE_BYTE,
    0x02: DATATYPE_UINT32,
    0x03: DATATYPE_UTF8,
    0x08: DATATYPE_UTF8,
    0x09: DATATYPE_BYTES,
    0x0B: DATATYPE_VAR_BYTE_INT,
    0x11: DATATYPE_UINT32,
    0x12: DATATYPE_UTF8,
    0x13: DATATYPE_UINT16,
    0x15: DATATYPE_UTF8,
    0x16: DATATYPE_BYTES,
    0x17: DATATYPE_BYTE,
    0x18: DATATYPE_UINT32,
    0x19: DATATYPE_BYTE,
    0x1A: DATATYPE_UTF8,
    0x1C: DATATYPE_UTF8,
    0x1F: DATATYPE_UTF8,
    0x21: DATATYPE_UINT16,
    0x22: DATATYPE_UINT16,
    0x23: DATATYPE_UINT16,
    0x24: DATATYPE_BYTE,
    0x25: DATATYPE_BYTE,
    0x26: DATATYPE_UTF8_PAIR,
    0x27: DATATYPE_UINT32,
    0x28: DATATYPE_BYTE,
    0x29: DATATYPE_BYTE,
    0x2A: DATATYPE_BYTE,
}

def write_byte(packet, value):
    packet.write_byte(value)

def write_uint16(packet, value):
    packet.write_uint16(value)

def write_uint32(packet, value):
    A = (value & 0xFFFF0000) >> 16
    packet.write_uint16(A)
    packet.write_uint16(value & 0xFFFF)

def write_varbyteint(packet, value):
    while True:
        flag   = value % 128
        value /= 128
        if value > 0:
            flag |= 128

        packet.write_byte(flag)

        if value <= 0:
            break

def write_bytes(packet, value):
    packet.write_bytes(value, len(value))

def write_utf8(packet, value):
    packet.write_string(value)

def write_utf8_pair(packet, (a,b)):
    packet.write_string(a)
    packet.write_string(b)

def read_byte(packet):
    return packet.read_byte()

def read_uint16(packet):
    return packet.read_uint16()

def read_uint32(packet):
    ret, msb = packet.read_uint16()
    ret, lsb = packet.read_uint16()
    return ret, (msb << 8) + lsb

def read_varint(packet):
    return packet.read_varint()

def read_bytes(packet):
    pass

def read_utf8(packet):
    pass

def read_utf8_pair(packet):
    ret, left = packet.read_string()
    ret, right = packet.read_string()

    return ret, (left, right)

DATATYPE_RW_OPS = {
    DATATYPE_BYTE        : [write_byte      , read_byte],
    DATATYPE_UINT16      : [write_uint16    , read_uint16],
    DATATYPE_UINT32      : [write_uint32    , read_uint32],
    DATATYPE_VAR_BYTE_INT: [write_varbyteint, read_varint],
    DATATYPE_BYTES       : [write_bytes     , read_bytes],
    DATATYPE_UTF8        : [write_utf8      , read_utf8],
    DATATYPE_UTF8_PAIR   : [write_utf8_pair , read_utf8_pair],
}

