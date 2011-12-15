'''
Nyamuk
Python Mosquitto Client Library
@author : Iwan Budi Kusnanto <iwan.b.kusnanto@gmail.com>
'''
import socket
import select
import time
import sys

from mqtt_pkt import MqttPkt
from MV import MV
import nyamuk_net
from nyamuk_msg import NyamukMsg, NyamukMsgAll
import mosquittod

MQTTCONNECT = 16# 1 << 4
class Nyamuk:
    def __init__(self, id = None, username = None, password = None, WITH_BROKER = False):
        ''' Constructor '''
        self.id = id
        
        if username != None:
            self.username = username
        else:
            self.username = None
        
        if password != None:
            self.password = password
        else:
            self.password = None
        
        self.address = ""
        self.keep_alive = MV.KEEPALIVE_VAL
        self.clean_session = False
        self.state = MV.CS_NEW
        self.last_msg_in = time.time()
        self.last_msg_out = time.time()
        self.last_mid = 0
        
        #output packet queue
        self.out_packet = []
        
        #input packet queue
        self.in_packet = MqttPkt()
        self.in_packet.packet_cleanup()
        
        #networking
        self.sock = MV.INVALID_SOCKET
        
        self.will = None
        
        
        self.in_callback = False
        self.message_retry = MV.MESSAGE_RETRY
        self.last_retry_check = 0
        self.messages = None
        
        
        #LOGGING:TODO
        self.log_priorities = -1
        self.log_destinations = -1
        
        #callback
        self.on_connect = None
        self.on_disconnect = None
        self.on_message = None
        self.on_publish = None
        self.on_subscribe = None
        self.on_unsubscribe = None
        
        self.host = None
        self.port = 1883
    
    def __del__(self):
        pass
    
    def connect(self, hostname = "localhost", port = 1883, keepalive = MV.KEEPALIVE_VAL, clean_session = True):
        
        self.hostnamne = hostname
        self.port = port
        self.keep_alive = keepalive
        self.clean_session = clean_session
        
        #CONNECT packet
        pkt = MqttPkt()
        print "Build Connect packet"
        pkt.connect_build(self, keepalive, clean_session)
        print "Build COnnect packet OK"
        
        #create socket
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        print "Connecting to server ...."
        ret = self.sock.connect((hostname, port))
        
        #set to nonblock
        self.sock.setblocking(0)
        
        print "Enqueueu packet"
        return self.packet_queue(pkt)
    
    def publish(self, topic, payload = None, qos = 0, retain = False):
        print "PUBLISHING"
        payloadlen = len(payload)
        if topic is None or qos < 0 or qos > 2:
            print "PUBLISH:err inval"
            return MV.ERR_INVAL
        
        if payloadlen > 268435455:
            print "PUBLISH:err payload"
            return MV.ERR_PAYLOAD_SIZE
        
        #wildcard check : TODO
        
        mid = self.mid_generate()
        
        if qos == 0:
            return self.send_publish(mid, topic, payload, qos, retain, False)
        else:
            print "Unsupport QoS=", qos
        pass
    
    def subscribe(self, mid, topic, qos):
        if self.sock == MV.INVALID_SOCKET:
            return MV.ERR_NO_CONN
        
        print "Sending SUBSCRIBE"
        return self.send_subscribe(mid, False, topic, qos)
        
    def send_subscribe(self, mid, dup, topic, qos):
        pkt = MqttPkt()
        
        pktlen = 2 + 2 + len(topic) + 1
        pkt.command = MV.CMD_SUBSCRIBE | (dup << 3) | (1 << 1)
        pkt.remaining_length = pktlen
        
        rc = pkt.alloc()
        if rc != MV.ERR_SUCCESS:
            return rc
        
        #variable header
        local_mid = self.mid_generate()
        mid = local_mid
        pkt.write_uint16(local_mid)
        
        #payload
        pkt.write_string(topic, len(topic))
        pkt.write_byte(qos)
        
        return self.packet_queue(pkt)
        
    def mid_generate(self):
        self.last_mid += 1
        if self.last_mid == 0:
            self.last_mid += 1
        return self.last_mid
    
    def packet_queue(self, pkt):
        '''
        Enqueue packet to out_packet queue
        '''
        
        pkt.pos = 0
        pkt.to_process = pkt.packet_length
        
        self.out_packet.append(pkt)
        
        if self.in_callback == False:
            return self.packet_write()
        else:
            return MV.ERR_SUCCESS
        
    def packet_write(self):
        if self.sock == MV.INVALID_SOCKET:
            return MV.ERR_NO_CONN
        
        while len(self.out_packet) > 0:
            pkt = self.out_packet[0]
            status, write_length = nyamuk_net.write(self.sock, pkt.payload)
            if write_length > 0:
                pkt.to_process -= write_length
                pkt.pos += write_length
                
                if pkt.to_process > 0:
                    return MV.ERR_SUCCESS
                else:
                    print "[packet_write]all packet sent, next packcet"
            else:
                if status == MV.NET_EAGAIN or status == MV.NET_EWOULDBLOCK:
                    return MV.ERR_SUCCESS
                elif status == MV.NET_COMPAT_ECONNRESET:
                    return MV.ERR_CONN_LOST
                else:
                    return MV.ERR_UNKNOWN
            
            if pkt.command & 0xF6 == MV.CMD_PUBLISH and self.on_publish is not None:
                self.in_callback = True
                self.on_publish(pkt.mid)
                self.in_callback = False
            
            #next
            del self.out_packet[0]
            
            #free data (unnecessary)
            
            self.last_msg_out = time.time()
            
        
        return MV.ERR_SUCCESS
    
    def loop(self, timeout = 1):
        rlist = [self.sock]
        wlist = []
        if len(self.out_packet) > 0:
            wlist.append(self.sock)
        
        to_read, to_write, in_error = select.select(rlist, wlist, [], timeout)
        
        if len(to_read) > 0:
            rc = self.loop_read()
            if rc != MV.ERR_SUCCESS:
                self.socket_close()
                if self.state == MV.CS_DISCONNECTING:
                    rc = MV.ERR_SUCCESS
                    
                if self.on_disconnect is not None:
                    self.in_callback = True
                    self.on_disconnect()
                    self.in_callback = False
                
                return rc
        
        if len(to_write) > 0:
            self.loop_write(to_write)
            
        self.loop_misc()
        
        return MV.ERR_SUCCESS
    
    def loop_read(self, WITH_BROKER = False):
        return self.packet_read(WITH_BROKER)
    
    def packet_read(self, WITH_BROKER = False):
        """Read packet."""
        if self.sock == MV.INVALID_SOCKET:
            return MV.ERR_NO_CONN
        
        if self.in_packet.command == 0:
            readlen, ba,status = nyamuk_net.read(self.sock, 1)
            
            if readlen == 1:
                byte = ba[0]
                self.in_packet.command = byte
                
                if WITH_BROKER == True:
                    #bytes_received++
                    if self.bridge is not None and self.state == MV.CS_NEW and (byte & 0xF) != MV.CMD_CONNECT:
                        return 1
                    
            else:
                if readlen == 0:
                    return MV.ERR_CONN_LOST
                if status == MV.NET_EAGAIN or status == MV.NET_EWOULDBLOCK:
                    return MV.ERR_SUCCESS
                else:
                    if status == MV.NET_COMPAT_ECONNRESET:
                        return MV.ERR_CONN_LOST
                    else:
                        return MV.ERR_UNKNOWN
                
        if self.in_packet.have_remaining == False:
            loop_flag = True
            while loop_flag == True:
                readlen, ba,status = nyamuk_net.read(self.sock, 1)
                byte = ba[0]
                if readlen == 1:
                    self.in_packet.remaining_count += 1
                    if self.in_packet.remaining_count > 4:
                        return MV.ERR_PROTOCOL
                    
                    self.in_packet.remaining_length += (byte & 127) * self.in_packet.remaining_mult
                    self.in_packet.remaining_mult *= 128
                else:
                    if readlen == 0:
                        return MV.ERR_CONN_LOST
                
                if (byte & 128) == 0:
                    loop_flag = False
            
            if self.in_packet.remaining_length > 0:
                self.in_packet.payload = bytearray(self.in_packet.remaining_length)
                if self.in_packet.payload is None:
                    return MV.ERR_NO_MEM
                self.in_packet.to_process = self.in_packet.remaining_length
            
            self.in_packet.have_remaining = True
            
        if self.in_packet.to_process > 0:
            readlen, ba, status = nyamuk_net.read(self.sock, self.in_packet.to_process)
            if readlen > 0:
                for x in range(0, readlen):
                    self.in_packet.payload[self.in_packet.pos] = ba[x]
                    self.in_packet.pos += 1
                    self.in_packet.to_process -= 1
            else:
                if status == MV.NET_EAGAIN or status == MV.NET_EWOULDBLOCK:
                    return MV.ERR_SUCCESS
                else:
                    if status == MV.NET_COMPAT_ECONNRESET:
                        return MV.ERR_CONN_LOST
                    else:
                        return MV.ERR_UNKNOWN
        
        #all data for this packet is read
        self.in_packet.pos = 0
        
        if WITH_BROKER == True:
            rc = self.packet_handle()
        else:
            rc = self.packet_handle()
        
        self.in_packet.packet_cleanup()
        
        self.last_msg_in = time.time()
        
        return rc
                
    def loop_write(self, wlist):
        pass
    
    def loop_misc(self):
        self.check_keepalive()
        if self.last_retry_check + 1  < time.time():
            pass
        return MV.ERR_SUCCESS
    
    def check_keepalive(self):
        #print "time - last_msg_out = ", time.time() - self.last_msg_out
        #print "keepalive = ", self.keep_alive
        if self.sock != MV.INVALID_SOCKET and time.time() - self.last_msg_out >= self.keep_alive:
            if self.state == MV.CS_CONNECTED:
                self.send_pingreq()
            else:
                self.socket_close()
                
    def socket_close(self):
        if self.sock != MV.INVALID_SOCKET:
            self.sock.close()
        self.sock = MV.INVALID_SOCKET
    
    def packet_handle(self):
        cmd = self.in_packet.command & 0xF0
        
        if cmd == MV.CMD_CONNACK:
            return self.handle_connack()
        elif cmd == MV.CMD_PINGRESP:
            return self.handle_pingresp()
        elif cmd == MV.CMD_PUBLISH:
            return self.handle_publish()
        elif cmd == MV.CMD_PUBACK:
            print "Received PUBACK"
            sys.exit(-1)
        elif cmd == MV.CMD_PUBREC:
            print "Received PUBREC"
            sys.exit(-1)
        elif cmd == MV.CMD_PUBREL:
            print "Received PUBREL"
            sys.exit(-1)
        elif cmd == MV.CMD_PUBCOMP:
            print "Received PUBCOMP"
            sys.exit(-1)
        elif cmd == MV.CMD_SUBSCRIBE:
            print "Received SUBSCRIBE"
            sys.exit(-1)
        elif cmd == MV.CMD_SUBACK:
            print "Received SUBACK"
            return self.handle_suback()
            
        elif cmd == MV.CMD_UNSUBSCRIBE:
            print "Received UNSUBSCRIBE"
            sys.exit(-1)
        elif cmd == MV.CMD_UNSUBACK:
            print "Received UNSUBACK"
            sys.exit(-1)
        else:
            print "Unknown protocol. Cmd = ", cmd
            return MV.ERR_PROTOCOL
    
    def handle_connack(self):
        print "Received CONNACK"
        rc, byte = self.in_packet.read_byte()
        if rc != MV.ERR_SUCCESS:
            print "faul"
            return rc
        
        rc, result = self.in_packet.read_byte()
        if rc != MV.ERR_SUCCESS:
            print "wataw"
            return rc
        
        if self.on_connect is not None:
            self.in_callback = True
            self.on_connect(result, self)
            self.in_callback = False
        
        if result == 0:
            self.state = MV.CS_CONNECTED
            print "Coooooonected"
            return MV.ERR_SUCCESS
        
        elif result >= 1 and result <= 5:
            return MV.ERR_CONN_REFUSED
        else:
            return MV.ERR_PROTOCOL
    
    def handle_pingresp(self):
        print "Received PINGRESP"
        return MV.ERR_SUCCESS
    
    def handle_suback(self):
        print "Received SUBACK"
        
        rc, mid = self.in_packet.read_uint16()
        
        if rc != MV.ERR_SUCCESS:
            return rc
        
        qos_count = self.in_packet.remaining_length - self.in_packet.pos
        granted_qos = bytearray(qos_count)
        
        if granted_qos is None:
            return MV.ERR_NO_MEM
        
        i = 0
        while self.in_packet.pos < self.in_packet.remaining_length:
            rc,byte = self.in_packet.read_byte()
            
            if rc != MV.ERR_SUCCESS:
                granted_qos = None
                return rc
            
            granted_qos[i] = byte
            
            i += 1
        
        if self.on_subscribe is not None:
            self.in_callback = True
            #self.on_subscribe(self, mid, qos_count, granted_qos)
            self.on_subscribe(self, mid, granted_qos)
            self.in_callback = False
        
        granted_qos = None
        
        return MV.ERR_SUCCESS
    
    def handle_publish(self):
        print "Received PUBLISH"
        
        header = self.in_packet.command
        
        message = NyamukMsgAll()
        message.direction = MV.DIRECTION_IN
        message.dup = (header & 0x08) >> 3
        message.msg.qos = (header & 0x06) >> 1
        message.msg.retain = (header & 0x01)
        
        rc, ba = self.in_packet.read_string()
        message.msg.topic = ba.decode()
        
        if rc != MV.ERR_SUCCESS:
            return rc
        
        #fix_sub_topic TODO
        
        if message.msg.qos > 0:
            rc, word = self.in_packet.read_uint16()
            message.msg.mid = word
            if rc != MV.ERR_SUCCESS:
                return rc
        
        message.msg.payloadlen = self.in_packet.remaining_length - self.in_packet.pos
        
        if message.msg.payloadlen > 0:
            rc, message.msg.payload = self.in_packet.read_bytes(message.msg.payloadlen)
            if rc != MV.ERR_SUCCESS:
                return rc
        
        print "Receied PUBLISH(d=",message.dup,",qos=",message.msg.qos,",retain=",message.msg.retain
        print "\tmid=",message.msg.mid,",topic=",message.msg.topic,",payloadlen=",message.msg.payloadlen
        
        message.timestamp = time.time()
        
        qos = message.msg.qos
        if qos == 0:
            if self.on_message is not None:
                self.in_callback = True
                self.on_message(self, message.msg)
                self.in_callback = False
            return MV.ERR_SUCCESS
        elif qos == 1 or qos == 2:
            print "handle_publish. Unsupported QoS = 1 or QoS = 2"
            sys.exit(-1)
        else:
            return MV.ERR_PROTOCOL
        
        
        return MV.ERR_SUCCESS
    def send_publish(self, mid, topic, payload, qos, retain, dup):
        if self.sock == MV.INVALID_SOCKET:
            return MV.ERR_NO_CONN
        return self.send_real_publish(mid, topic, payload, qos, retain, dup)
    
    def send_real_publish(self, mid, topic, payload, qos, retain, dup):
        pkt = MqttPkt()
        payloadlen = len(payload)
        packetlen = 2 + len(topic) + payloadlen
        
        if qos > 0:
            packetlen += 2
        
        pkt.mid = mid
        pkt.command = MV.CMD_PUBLISH | ((dup & 0x1) << 3) | (qos << 1) | retain
        pkt.remaining_length = packetlen
        
        rc = pkt.alloc()
        if rc != MV.ERR_SUCCESS:
            return rc
        
        #variable header : Topic String
        pkt.write_string(topic, len(topic))
        
        if qos > 0:
            pkt.write_uint16(mid)
        
        #payloadlen
        if payloadlen > 0:
            pkt.write_bytes(payload, payloadlen)
        
        return self.packet_queue(pkt)
        
    def send_pingreq(self):
        print "SEND PINGREQ"
        self.send_simple_command(MV.CMD_PINGREQ)
    
    def send_simple_command(self, cmd):
        pkt = MqttPkt()
        
        pkt.command = cmd
        pkt.remaining_length = 0
        
        rc = pkt.alloc()
        if rc != MV.ERR_SUCCESS:
            return rc
        
        return self.packet_queue(pkt)