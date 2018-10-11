'''
MQTT Packet
@author : Iwan Budi Kusnanto
'''
import sys

from utils import *
import nyamuk_const as NC
import nyamuk_net
from nyamuk_prop import *
import mqtt_types as t

class MqttPkt:
    """An mqtt packet."""
    def __init__(self):
        self.command = 0
        self.have_remaining = False
        self.remaining_count = 0
        self.mid = 0
        self.remaining_mult = 1
        self.remaining_length = 0
        self.packet_length = 0

        #len of packet to write
        self.to_process = 0

        #packet cursor
        self.pos = 0

        self.payload = None

        #self.next = None

    def dump(self):
        """Print packet content."""
        print "-----MqttPkt------"
        print "command = ", self.command
        print "have_remaining = ", self.have_remaining
        print "remaining_count = ", self.remaining_count
        print "mid = ", self.mid
        print "remaining_mult = ", self.remaining_mult
        print "remaining_length = ", self.remaining_length
        print "packet_length = ", self.packet_length
        print "to_process = ", self.to_process
        print "pos = ", self.pos
        print "payload = ", self.payload
        print "------------------"

    def alloc(self):
        """from _mosquitto_packet_alloc."""
        byte = 0
        remaining_bytes = bytearray(5)
        i = 0

        remaining_length = self.remaining_length

        self.payload = None
        self.remaining_count = 0
        loop_flag = True

        #self.dump()
        # computing remaining length field
        # is a varint (from 1 to 4 bytes)
        while loop_flag:
            byte = remaining_length % 128
            remaining_length = remaining_length / 128

            if remaining_length > 0:
                byte = byte | 0x80

            remaining_bytes[self.remaining_count] = byte
            self.remaining_count += 1

            if not (remaining_length > 0 and self.remaining_count < 5):
                loop_flag = False

        if self.remaining_count == 5:
            return NC.ERR_PAYLOAD_SIZE

        # MQTT header (1 byte) + remaining length count + headers & payload
        self.packet_length = 1 + self.remaining_count + self.remaining_length
        #print('allocating {0} bytearray (remaining lengh field size= {1})'.format(
        #    self.packet_length, self.remaining_count))
        self.payload = bytearray(self.packet_length)

        self.payload[0] = self.command

        i = 0
        while i < self.remaining_count:
            self.payload[i+1] = remaining_bytes[i]
            i += 1

        self.pos = 1 + self.remaining_count

        return NC.ERR_SUCCESS

    def packet_cleanup(self):
        self.command = 0
        self.have_remaining = False
        self.remaining_count = 0
        self.remaining_mult = 1
        self.remaining_length = 0
        self.payload = None
        self.to_process = 0
        self.pos = 0

    def connect_build(self, nyamuk, keepalive, clean_session, retain = 0, dup = 0, version = 3,
            props = []):
        """Build packet for CONNECT command."""
        will = 0; will_topic = None
        byte = 0

        specs = NC.specs[version]

        props_len = 0
        if version >= 5:
            props_len = reduce(lambda x,y: x + y.len(), props, 0)

        client_id = '' if nyamuk.client_id is None else utf8encode(nyamuk.client_id)
        username  = utf8encode(nyamuk.username) if nyamuk.username is not None else None
        password  = utf8encode(nyamuk.password) if nyamuk.password is not None else None

        # payload len
        payload_len = t.len_utf8(client_id)
        props = []; props_len = 0
        if nyamuk.will is not None:
            will = 1
            will_topic = utf8encode(nyamuk.will.topic)

            payload_len += t.len_utf8(will_topic) + 2 + nyamuk.will.payloadlen

            if version >= 5:
                will_props_len = reduce(lambda x, y: x + y.len(), nyamuk.will.props, 0)
                payload_len += will_props_len + t.len_varint(will_props_len)

        if username is not None:
            payload_len = payload_len + 2 + len(username)
            if password != None:
                payload_len = payload_len + 2 + len(password)

        self.command = NC.CMD_CONNECT
        self.remaining_length = specs['hdrsize'] + payload_len + props_len + \
            t.len_varint(props_len)
        #print("len=", self.remaining_length, payload_len, props_len, t.len_varint(props_len))

        rc = self.alloc()
        if rc != NC.ERR_SUCCESS:
            return rc

        # var header
        self.write_utf8(specs['name'])
        self.write_byte(version)

        byte = (clean_session & 0x1) << 1

        if will:
            byte = byte | ((nyamuk.will.retain & 0x1) << 5) | ((nyamuk.will.qos & 0x3) << 3) | ((will & 0x1) << 2)

        if nyamuk.username is not None:
            byte = byte | 0x1 << 7
            if nyamuk.password is not None:
                byte = byte | 0x1 << 6

        self.write_byte(byte)
        self.write_uint16(keepalive)

        ## mqtt5: properties
        if version >= 5:
            self.write_props(props, props_len)

        # payload
        self.write_utf8(client_id)

        if will:
            if version >= 5:
                # 5.0 version: will content encoded as properties
                self.write_props(nyamuk.will.props, will_props_len)

            self.write_utf8(will_topic)
            self.write_utf8(nyamuk.will.payload)

        if username is not None:
            self.write_utf8(username)
            if password is not None:
                self.write_utf8(password)

        nyamuk.keep_alive = keepalive

        return NC.ERR_SUCCESS

    def write_byte(self, byte):
        """Write one byte."""
        #print('write byte:', self.pos)
        self.payload[self.pos] = byte
        self.pos = self.pos + 1

    def write_uint16(self, word):
        """Write 2 bytes."""
        self.write_byte(nyamuk_net.MOSQ_MSB(word))
        self.write_byte(nyamuk_net.MOSQ_LSB(word))

    def write_uint32(self, value):
        """Write 4 bytes."""
        self.payload[self.pos]   = value & 0xFF000000 >> 24
        self.payload[self.pos+1] = value & 0x00FF0000 >> 16
        self.payload[self.pos+2] = value & 0x0000FF00 >> 8
        self.payload[self.pos+3] = value & 0x000000FF

        self.pos = self.pos + 4

    def write_varint(self, value):
        while True:
            enc    = value % 128
            value /= 128
            if value > 0:
                enc |= 128

            self.write_byte(enc)

            if value <= 0:
                break


    def write_bytes(self, data, length=-1):
        """Write a bytearray to this packet.

            NOTE: data must be of bytearray type
        """
        if length < 0:
            length = len(data)

        self.write_uint16(length)
        self.payload[self.pos:self.pos+length] = data[:length]
        self.pos += len(data)

    def write_raw(self, data, length=-1):
        """`write_raw` is almost equivalent to `write_bytes`
            except we don't write data length in the destination buffer

            (the data written is not of MQTT types)
        """
        if length < 0:
            length = len(data)

        self.payload[self.pos:self.pos+length] = data[:length]
        self.pos += len(data)

    def write_utf8(self, string):
        """Write a string to this packet.

            NOTE: string is an encoded utf8 string (type str in py2.7)
        """
        string = utf8encode(string)
        #NOTE: byte length is written by write_bytes()
        self.write_bytes(bytearray(string))

    def write_utf8_pair(self, (key, value)):
        self.write_utf8(key)
        self.write_utf8(value)

    def write_props(self, props, propslen=None):
        propslen = propslen if propslen is not None else reduce(lambda x, y: x + y.len(), props, 0)
        self.write_varint(propslen)
        for p in props:
            p.write(self)

    def read_byte(self):
        """Read a byte."""
        if self.pos + 1 > self.remaining_length:
            return NC.ERR_PROTOCOL, None

        byte = self.payload[self.pos]
        self.pos += 1

        return NC.ERR_SUCCESS, byte

    def read_uint16(self):
        """Read 2 bytes."""
        if self.pos + 2 > self.remaining_length:
            return NC.ERR_PROTOCOL
        msb = self.payload[self.pos]
        self.pos += 1
        lsb = self.payload[self.pos]
        self.pos += 1

        word = (msb << 8) + lsb

        return NC.ERR_SUCCESS, word

    def read_uint32(self):
        """Read 4 bytes.

            NOTE: use struct.unpack
        """
        if self.pos + 4 > self.remaining_length:
            return NC.ERR_PROTOCOL
        a = self.payload[self.pos]
        b = self.payload[self.pos+1]
        c = self.payload[self.pos+2]
        d = self.payload[self.pos+3]
        self.pos += 4

        word = (a << 24) + (b << 16) + (c << 8) + d

        return NC.ERR_SUCCESS, word

    def read_varint(self):
        lshift = 0
        value  = 0

        for i in range(4):
            byte      = self.payload[self.pos]
            self.pos += 1
            value     = (byte & 0x7F) << lshift
            if byte & 0x80 == 0:
                break

            lshift += 7

        if byte & 0x80 != 0:
            raise Exception("varint overflow")

        return NC.ERR_SUCCESS, value

    def read_bytes(self):
        """Read count number of bytes."""
        rc, length = self.read_uint16()
        if rc != NC.ERR_SUCCESS:
            return rc, None

        if self.pos + length > self.remaining_length:
            return NC.ERR_PROTOCOL, None

        ba = self.payload[self.pos:self.pos+length]
        self.pos += length

        return NC.ERR_SUCCESS, ba

    def read_raw(self, length):
        """Read a raw byte stream (not a MQTT bytes type)
        """
        if self.pos + length > self.remaining_length:
            return NC.ERR_PROTOCOL, None

        raw = self.payload[self.pos:self.pos+length]
        self.pos += length

        return NC.ERR_SUCCESS, raw

    def read_utf8(self):
        """Read utf-8 string.
        """
        rc, length = self.read_uint16()

        if rc != NC.ERR_SUCCESS:
            return rc, None

        if self.pos + length > self.remaining_length:
            return NC.ERR_PROTOCOL, None

        ba = self.payload[self.pos:self.pos+length]
        self.pos += length
        if ba is None:
            return NC.ERR_NO_MEM, None

        return NC.ERR_SUCCESS, ba.decode('utf8')

    def read_utf8_pair(self):
        ret, key   = self.read_utf8()
        ret, value = self.read_utf8()

        return ret, (key, value)

    def read_props(self):
        """
            read properties
        """
        ret, props_len = self.read_varint()
        if props_len == 0:
            return NC.ERR_SUCCESS, []

        #print("read props")
        curlen = 0
        props  = []
        while True:
            ret, prop_id = self.read_varint()
            prop_type    = get_property_type(prop_id)
            #TODO: check returned value
            ret, value   = getattr(self, t.DATATYPE_OPS[prop_type][t.DATATYPE_RD])()

            prop = get_property_instance(prop_id, value)
            props.append(prop)
            curlen += prop.len()
            #print(ret, prop_name, prop_type, value, curlen)
            if curlen >= props_len:
                break

        if curlen != props_len:
            # invalid count: must close connection
            return NC.INVAL

        return NC.ERR_SUCCESS, props

