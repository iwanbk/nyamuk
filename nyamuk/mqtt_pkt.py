'''
MQTT Packet
@author : Iwan Budi Kusnanto
'''
from MV import MV
import nyamuk_net
import nyamuk



class MqttPkt:
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
        print "-----MqttPkt------"
        print "command = ", self.command
        print "have_remaining = ", self.have_remaining
        print "remaining_count = ", self.remaining_count
        print "mid = ",self.mid
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
        while loop_flag == True:
            byte = remaining_length % 128
            remaining_length = remaining_length / 128
            
            if remaining_length > 0:
                byte = byte | 0x80
                
            remaining_bytes[self.remaining_count] = byte
            self.remaining_count += 1
            
            if not (remaining_length > 0 and self.remaining_count < 5):
                loop_flag = False
        
        if self.remaining_count == 5:
            return MV.ERR_PAYLOAD_SIZE
        
        self.packet_length = self.remaining_length + 1 + self.remaining_count
        self.payload = bytearray(self.packet_length)
        
        self.payload[0] = self.command
        
        i = 0
        while i < self.remaining_count:
            self.payload[i+1] = remaining_bytes[i]
            i += 1
        
        self.pos = 1 + self.remaining_count
        
        return MV.ERR_SUCCESS
    
    def packet_cleanup(self):
        self.command = 0
        self.have_remaining = False
        self.remaining_count = 0
        self.remaining_mult = 1
        self.remaining_length = 0
        self.payload = None
        self.to_process = 0
        self.pos = 0
    
    def connect_build(self, nyamuk, keepalive, clean_session,retain = 0, dup = 0):
        will = 0
        byte = 0
        
        #payload len
        payload_len = 2 + len(nyamuk.id)
        if nyamuk.will is not None:
            will = 1
            payload_len = payload_len + 2 + len(nyamuk.will.topic) + 2 + nyamuk.will.payloadlen
        
        if nyamuk.username is not None:
            payload_len = payload_len + 2 + len(nyamuk.username)
            if nyamuk.password != None:
                payload_len = payload_len + 2 + len(nyamuk.password)
        
        self.command = MV.CONNECT
        self.remaining_length = 12 + payload_len
    
        rc = self.alloc()
        if rc != MV.ERR_SUCCESS:
            return rc
         
        #var header
        self.write_string(MV.PROTOCOL_NAME, len(MV.PROTOCOL_NAME))
        self.write_byte(MV.PROTOCOL_VERSION)
        
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
        self.write_string(nyamuk.id, len(nyamuk.id))
        
        if will:
            pass #TODO
        if nyamuk.username is not None:
            pass #TODO
        
        nyamuk.keep_alive = keepalive
    
    def write_string(self, str, length):
        '''
        char *str
        uint16_t length
        '''
        self.write_uint16(length)
        self.write_bytes(str, length)
        
    def write_uint16(self, word):
        '''
        uint16_t word
        '''
        self.write_byte(nyamuk_net.MOSQ_MSB(word))
        self.write_byte(nyamuk_net.MOSQ_LSB(word))
        
    def write_byte(self, byte):
        '''
        uint8_t byte
        '''
        self.payload[self.pos] = byte
        self.pos = self.pos + 1
    
    def write_bytes(self, bytes, count):
        #memcpy(&(packet->payload[packet->pos]), bytes, count);
        
        #print "count = ", count
        for pos in range(0, count):
            #print "pos = ",pos
            self.payload[self.pos + pos] = bytes[pos]
            
        self.pos += count
    
    def read_byte(self):
        if self.pos + 1 > self.remaining_length:
            return MV.ERR_PROTOCOL, None
        
        byte = self.payload[self.pos]
        self.pos += 1
        
        return MV.ERR_SUCCESS, byte
    
    def read_uint16(self):
        if self.pos + 2 > self.remaining_length:
            return MV.ERR_PROTOCOL
        msb = self.payload[self.pos]
        self.pos += 1
        lsb = self.payload[self.pos]
        self.pos += 1
        
        word = (msb << 8) + lsb
        
        return MV.ERR_SUCCESS, word
    
    def read_bytes(self, count):
        if self.pos + count > self.remaining_length:
            return MV.ERR_PROTOCOL, None
        
        ba = bytearray(count)
        for x in range(0, count):
            ba[x] = self.payload[self.pos]
            self.pos += 1
        
        return MV.ERR_SUCCESS, ba
    
    def read_string(self):
        rc, len = self.read_uint16()
        
        if rc != MV.ERR_SUCCESS:
            print "1"
            return rc, None
        
        if self.pos + len > self.remaining_length:
            print "2. len = ", len, " remaining_length = ", self.remaining_length, " POS =", self.pos
            return MV.ERR_PROTOCOL, None
        
        ba = bytearray(len)
        if ba is None:
            print 3
            return MV.ERR_NO_MEM, None
        
        for x in range(0, len):
            ba[x] = self.payload[self.pos]
            self.pos += 1
        
        return MV.ERR_SUCCESS, ba 
        
def fixhdr_build(qos =0, retain = 0, dup = 0):
    pass
