'''
Nyamuk
Python Mosquitto Client Library
@author : Iwan Budi Kusnanto <iwan.b.kusnanto@gmail.com>
'''
import socket
import select

from mqtt_pkt import MqttPkt
from MV import MV

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
        self.last_msg_in = None
        self.last_msg_out = None
        self.last_mid = -1
        
        #output packet queue
        self.out_packet = []
        
        #input packet queue
        self.in_packet = []
        
        #networking
        self.sock = -1
        
        
        self.in_callback = False
        self.message_retry = MV.MESSAGE_RETRY
        self.last_retry_check = 0
        self.messages = None
        self.will = None
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
        
        print "Connecting....."
        ret = self.sock.connect((hostname, port))
        print "Connected.....to host"
        
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
    
    def loop(self, timeout):
        rlist = [self.sock]
        wlist = []
        if len(self.out_packet) > 0:
            wlist.append(self.sock)
        
        to_read, to_write, in_error = select.select(rlist, wlist, None)
        
        self.loop_read(to_read)
        self.loop_write(to_write)
        self.loop_misc()
        
        return MV.ERR_SUCCESS
    
    def loop_read(self, rlist):
        pass
    def loop_write(self, wlist):
        pass
    def loop_misc(self):
        pass