#!/usr/bin/env python
# -*- coding: utf8 -*-

DATATYPE_BYTE      = 0x01
DATATYPE_UINT16    = 0x02
DATATYPE_UINT32    = 0x03
DATATYPE_VARINT    = 0x04
DATATYPE_BYTES     = 0x05
DATATYPE_UTF8      = 0x06
DATATYPE_UTF8_PAIR = 0x07

def len_bytes(value):
    """
        bytearray
    """
    return 2 + len(value)

def len_varint(value):
    """
        val: (possibly large) integer

        0 - 127   : 1 byte
        128 - 2^14: 2 bytes
        ...
    """
    if value == 0:
        return 1

    count = 0
    while value > 0:
        value /= 128
        count += 1

    if count > 4:
        raise Exception("up to 4 bytes")

    return count

def len_utf8(value):
    """
        utf8 string
    """
    return 2 + len(value)

def len_utf8_pair((key, value)):
        return 4 + len(key) + len(value)

DATATYPE_LEN = 0
DATATYPE_WR  = 1
DATATYPE_RD  = 2

# len_ methods are local
# write_ & read_ methods are MqttPkt instance methods
# (must be invoked with getattr())
DATATYPE_OPS = {
    DATATYPE_BYTE        : [1            , 'write_byte'     , 'read_byte'],
    DATATYPE_UINT16      : [2            , 'write_uint16'   , 'read_uint16'],
    DATATYPE_UINT32      : [4            , 'write_uint32'   , 'read_uint32'],
    DATATYPE_VARINT      : [len_varint   , 'write_varint'   , 'read_varint'],
    DATATYPE_BYTES       : [len_bytes    , 'write_bytes'    , 'read_bytes'],
    DATATYPE_UTF8        : [len_utf8     , 'write_utf8'     , 'read_utf8'],
    DATATYPE_UTF8_PAIR   : [len_utf8_pair, 'write_utf8_pair', 'read_utf8_pair'],
}

