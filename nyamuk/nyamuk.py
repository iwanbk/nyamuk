'''
Nyamuk
Python Mosquitto Client Library
@author : Iwan Budi Kusnanto <iwan.b.kusnanto@gmail.com>
'''
import socket
import select
import time

from mqtt_pkt import MqttPkt
from MV import MV
import nyamuk_net

MQTTCONNECT = 16# 1 << 4
class Nyamuk:
    def __init__(self, id, username = None, password = None):
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
        
        
        self.in_callback = False
        self.message_retry = MV.MESSAGE_RETRY
        self.last_retry_check = 0
        self.messages = None
        self.will = None
        
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
    
    def connect(self, hostname = "localhost", port = 1883, keepalive = 60, clean_session = True):
        
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
        for pkt in self.out_packet:
            #pkt.dump()
            write_length = self.sock.send(pkt.payload)
            if write_length > 0:
                pkt.to_process -= write_length
                pkt.pos += write_length
                
                if pkt.to_process > 0:
                    return MV.ERR_SUCCESS
                else:
                    print "[packet_write]all packet sent, next packcet"
            else:
                return MV.ERR_SUCCESS
        
        return MV.ERR_SUCCESS
    
    def loop(self, timeout = 1):
        rlist = [self.sock]
        wlist = []
        if len(self.out_packet) > 0:
            wlist.append(self.sock)
        
        to_read, to_write, in_error = select.select(rlist, wlist, [], timeout)
        
        if len(to_read) > 0:
            rc = self.loop_read(to_read)
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
    
    def loop_read(self, rlist):
        '''
        read loop
        '''
        
        if self.sock == MV.INVALID_SOCKET:
            return MV.ERR_NO_CONN
        
        if self.in_packet.command == 0:
            readlen, ba,status = nyamuk_net.read(self.sock, 1)
            byte = ba[0]
            if readlen == 1:
                self.in_packet.command = byte
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
        
        rc = self.packet_handle()
        
        self.last_msg_in = time.time()
        
        return rc
                
    def loop_write(self, wlist):
        pass
    def loop_misc(self):
        pass
    
    def socket_close(self):
        pass
    
    def packet_handle(self):
        cmd = self.in_packet.command & 0xF0
        
        if cmd == MV.CMD_CONNACK:
            return self.handle_connack()
        else:
            print "Unknown protocol"
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
            self.on_connect(result)
            self.in_callback = False
        
        if result == 0:
            self.state = MV.CS_CONNECTED
            print "Coooooonected"
            return MV.ERR_SUCCESS
        
        elif result >= 1 and result <= 5:
            return MV.ERR_CONN_REFUSED
        else:
            return MV.ERR_PROTOCOL