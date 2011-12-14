'''
@author : Iwan Budi Kusnanto <iwan.b.kusnanto@gmail.com>
'''
import sys

import nyamuk
from MV import MV
from mqtt_pkt import MqttPkt

class Bee(nyamuk.Nyamuk):
    def __init__(self, sock, addr, conn_mgr, subs_mgr):
        nyamuk.Nyamuk.__init__(self)
        
        #from nyamuk
        self.sock = sock
        
        self.bridge = None
        self.msgs = None
        self.acl_list = None
        self.listener = None
        self.addr = addr
        
        self.cm = conn_mgr
        self.sm = subs_mgr  #subscription manager attached to this bee
    
    def packet_handle(self):
        """Packet Handling Dispatcher."""
        cmd = self.in_packet.command & 0xF0
        
        if cmd == MV.CMD_CONNECT:
            return self.handle_connect()
        elif cmd == MV.CMD_SUBSCRIBE:
            return self.handle_subscribe()
        else:
            print "Unsupport CMD = ", cmd
            return MV.ERR_NOT_SUPPORTED
    
    def handle_connect(self):
        """Handle CONNECT command."""
        print "Connecting client = ", self.addr
    
        if self.state != MV.CS_NEW:
            self.disconnect()
            return MV.ERR_PROTOCOL
        
        rc, ba = self.in_packet.read_string()
        if rc != MV.ERR_SUCCESS:
            self.disconnect()
            return 1
        
        protocol_name = ba.decode()
        
        #Protocol Name
        if protocol_name != MV.PROTOCOL_NAME:
            print "INVALID Protocol in Connect from ", self.addr
            self.disconnect()
            return MV.ERR_PROTOCOL
        
        #Protocol Version
        rc, protocol_version = self.in_packet.read_byte()
        if rc != MV.ERR_SUCCESS or protocol_version != MV.PROTOCOL_VERSION:
            print "INVALID PROTOCOL VERSIOON"
            self.disconnect()
            return MV.ERR_PROTOCOL
        
        #Connect Flags
        rc, connect_flags = self.in_packet.read_byte()
        if rc != MV.ERR_SUCCESS:
            self.disconnect()
            return 1
        
        clean_session = connect_flags & 0x02
        will = connect_flags & 0x04
        will_qos = (connect_flags & 0x18) >> 3
        will_retain = connect_flags & 0x20
        password_flag = connect_flags & 0x40
        username_flag = connect_flags & 0x80
        
        rc, self.keepalive = self.in_packet.read_uint16()
        if rc != MV.ERR_SUCCESS:
            self.disconnect()
            return 1
        
        rc, client_id = self.in_packet.read_string()
        if rc != MV.ERR_SUCCESS:
            self.disconnect()
            return 1
        
        #client ID prefixes check
        
        if will != 0:
            print "WILL Unsupported "
            sys.exit(-1)
        
        if username_flag != 0:
            print "username Unsupported"
            sys.exit(-1)
        
        self.id = client_id.decode()
        self.clean_session = clean_session
        
        if self.will is not None:
            print "WILL Unsupported "
            sys.exit(-1)
        
        #ACL
        
        self.cm.add(self)
        
        print "New client connected from ", self.addr
        
        return self.send_connack(0)
        
    def handle_subscribe(self):
        qos = 0
        payload = bytearray(0)
        payloadlen = 0
        
        print "Handle subscribe from : ", self.id, " at ", self.addr
        
        rc, mid = self.in_packet.read_uint16()
        if rc != MV.ERR_SUCCESS:
            return 1
        
        while self.in_packet.pos < self.in_packet.remaining_length:
            rc, ba_sub = self.in_packet.read_string()
            if rc != MV.ERR_SUCCESS:
                return 1
            
            if len(ba_sub) == 0:
                print "Empty Subscription from ", self.id, ". Disconnecting.."
            
            sub = ba_sub.decode()
            
            rc, qos = self.in_packet.read_byte()
            if rc != MV.ERR_SUCCESS:
                return 1
                
            if qos > 2 or qos < 0:
                #TODO
                sys.exit(-1)
                
            #fix subtopic TODO
                
            rc = self.sm.add(self, sub, qos)
            
            if rc == MV.ERR_SUCCESS:
                sys.exit(-1)
            
            payload.append(qos)
            payloadlen += 1
        
        rc = self.send_suback(mid, payloadlen, payload)
        
    def disconnect(self):
        print "[mqtt3_context_disconnect]Unimplemented Func"
        self.socket_close()
        sys.exit(-1)
    
    
    def send_connack(self, result):
        """Send CONNACK command to client."""
        pkt = MqttPkt()
        
        pkt.command = MV.CMD_CONNACK
        pkt.remaining_length = 2
        
        pkt.alloc()
        
        pkt.payload[pkt.pos + 0] = 0
        pkt.payload[pkt.pos + 1] = result
        
        return self.packet_queue(pkt)
    
    def send_suback(self, mid, payloadlen, payload):
        pkt = MqttPkt()
        pkt.command = MV.CMD_SUBACK
        pkt.remaining_length = 2 + payloadlen
        
        rc = pkt.alloc()
        if rc != MV.ERR_SUCCESS:
            return rc
        
        pkt.write_uint16(mid)
        if payloadlen > 0:
            pkt.write_bytes(payload, payloadlen)
        
        return self.packet_queue(pkt)