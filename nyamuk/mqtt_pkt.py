'''
MQTT Packet
@author : Iwan Budi Kusnanto
'''
import sys

from utils import utf8encode
import nyamuk_const as NC
import nyamuk_net

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
        
        self.packet_length = self.remaining_length + 1 + self.remaining_count
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
    
    def connect_build(self, nyamuk, keepalive, clean_session, retain = 0, dup = 0, version = 3):
        """Build packet for CONNECT command."""
        will = 0; will_topic = None
        byte = 0

        client_id = utf8encode(nyamuk.client_id)
        username  = utf8encode(nyamuk.username) if nyamuk.username is not None else None
        password  = utf8encode(nyamuk.password) if nyamuk.password is not None else None

        #payload len
        payload_len = 2 + len(client_id)
        if nyamuk.will is not None:
            will = 1
            will_topic = utf8encode(nyamuk.will.topic)

            payload_len = payload_len + 2 + len(will_topic) + 2 + nyamuk.will.payloadlen
        
        if username is not None:
            payload_len = payload_len + 2 + len(username)
            if password != None:
                payload_len = payload_len + 2 + len(password)
        
        self.command = NC.CMD_CONNECT
        self.remaining_length = 12 + payload_len
    
        rc = self.alloc()
        if rc != NC.ERR_SUCCESS:
            return rc
         
        #var header
        self.write_string(getattr(NC, 'PROTOCOL_NAME_{0}'.format(version)))
        self.write_byte(  getattr(NC, 'PROTOCOL_VERSION_{0}'.format(version)))
        
        byte = (clean_session & 0x1) << 1
        
        if will:
            byte = byte | ((nyamuk.will.retain & 0x1) << 5) | ((nyamuk.will.qos & 0x3) << 3) | ((will & 0x1) << 2)
        
        if nyamuk.username is not None:
            byte = byte | 0x1 << 7
            if nyamuk.password is not None:
                byte = byte | 0x1 << 6
        
        self.write_byte(byte)
        self.write_uint16(keepalive)
        #payload
        self.write_string(client_id)
        
        if will:
            self.write_string(will_topic)
            self.write_string(nyamuk.will.payload)

        if username is not None:
            self.write_string(username)
            if password is not None:
                self.write_string(password)
            
        nyamuk.keep_alive = keepalive
        
        return NC.ERR_SUCCESS
    
    def write_string(self, string):
        """Write a string to this packet."""
        self.write_uint16(len(string))
        self.write_bytes(string, len(string))
        
    def write_uint16(self, word):
        """Write 2 bytes."""
        self.write_byte(nyamuk_net.MOSQ_MSB(word))
        self.write_byte(nyamuk_net.MOSQ_LSB(word))
        
    def write_byte(self, byte):
        """Write one byte."""
        self.payload[self.pos] = byte
        self.pos = self.pos + 1
    
    def write_bytes(self, data, n):
        """Write n number of bytes to this packet."""
        for pos in xrange(0, n):
            self.payload[self.pos + pos] = data[pos]
            
        self.pos += n
    
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
    
    def read_bytes(self, count):
        """Read count number of bytes."""
        if self.pos + count > self.remaining_length:
            return NC.ERR_PROTOCOL, None
        
        ba = bytearray(count)
        for x in xrange(0, count):
            ba[x] = self.payload[self.pos]
            self.pos += 1
        
        return NC.ERR_SUCCESS, ba
    
    def read_string(self):
        """Read string."""
        rc, length = self.read_uint16()
        
        if rc != NC.ERR_SUCCESS:
            return rc, None
        
        if self.pos + length > self.remaining_length:
            return NC.ERR_PROTOCOL, None
        
        ba = bytearray(length)
        if ba is None:
            return NC.ERR_NO_MEM, None
        
        for x in xrange(0, length):
            ba[x] = self.payload[self.pos]
            self.pos += 1
        
        return NC.ERR_SUCCESS, ba
