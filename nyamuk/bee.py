'''
@author : Iwan Budi Kusnanto <iwan.b.kusnanto@gmail.com>
'''
import sys
import select

import gevent
from gevent import queue

import base_nyamuk
from MV import MV
from mqtt_pkt import MqttPkt

class Bee(base_nyamuk.BaseNyamuk):
    def __init__(self, sock, addr, conn_mgr, subs_mgr, logger):
        base_nyamuk.BaseNyamuk.__init__(self)
        
        #from nyamuk
        self.sock = sock
        
        self.bridge = None
        self.msgs = None
        self.acl_list = None
        self.listener = None
        self.addr = addr
        
        self.logger = logger
        self.cm = conn_mgr
        self.sm = subs_mgr  #subscription manager attached to this bee
        
        self.pkt_mq = queue.Queue(10)
        
        self.as_broker = True
    
    def __del__(self):
        print "DELETING Bee Object : ", self.id, " ", self.addr
        if self.sock != MV.INVALID_SOCKET:
            print "Closing the socket"
            self.socket_close()
    
    def _send_pkt(self, pkt):
        print "Queueing publish_pkt to ", self.id
        self.pkt_mq.put(pkt)
    
    def _get_list_pkt(self):
        if self.pkt_mq.empty() == True:
            return []
        lp = []
        pkt = self.pkt_mq.get(False)
        lp.append(pkt)
        return lp
        
    def loop(self, timeout = 1):
        rlist = [self.sock]
        wlist = []
        rc = MV.ERR_SUCCESS
        
        pkt = None
        
        lp = self._get_list_pkt()
        
        if len(lp) > 0:
            print "id= ", self.id, " #LP Size = ", len(lp)
            for i in range(0, len(lp)):
                self.packet_queue(lp[i])
                
        if len(self.out_packet) > 0:
            wlist.append(self.sock)
        
        readable, writable, exceptional = select.select(rlist, wlist, [], timeout)
        if len(readable) > 0:
            rc = self.packet_read()
            if rc != MV.ERR_SUCCESS:
                return rc
        
        if len(writable) > 0:
            rc = self.packet_write()
            if rc != MV.ERR_SUCCESS:
                return rc
        
        return rc
        
    def packet_handle(self):
        """Packet Handling Dispatcher."""
        cmd = self.in_packet.command & 0xF0
        
        if cmd == MV.CMD_CONNECT:
            return self.handle_connect()
        elif cmd == MV.CMD_SUBSCRIBE:
            return self.handle_subscribe()
        elif cmd == MV.CMD_PINGREQ:
            return self.handle_pingreq()
        elif cmd == MV.CMD_PUBLISH:
            return self.handle_publish()
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
        self.logger.logger.info("New client connected from %s", self.addr)
        
        self.state = MV.CS_CONNECTED
        return self.send_connack(0)
        
    def handle_subscribe(self):
        """Handle SUBSCRIBE."""
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
        
        return rc
    
    def handle_pingreq(self):
        """Handle PINGREQ."""
        if self.in_packet.remaining_length != 0:
            return MV.ERR_PROTOCOL
        
        self.logger.logger.debug("Received PINGREQ from %s", self.id)
        
        return self.send_pingresp()
    
    def handle_publish(self):
        header = self.in_packet.command
        
        dup = (header & 0x08) >> 3
        qos = (header & 0x06) >> 1
        retain = (header & 0x01)
        
        rc, ba_topic = self.in_packet.read_string()
        if rc != MV.ERR_SUCCESS:
            return 1
        
        topic = str(ba_topic)
        rc, topic = self._fix_subtopic(topic)
        if rc != MV.ERR_SUCCESS:
            return 1
        
        if self._wildcard_check(topic) == True:
            return MV.ERR_SUCCESS
        
        mid = 0
        if qos > 0:
            rc, mid = self.in_packet.read_uint16()
            if rc != MV.ERR_SUCCESS:
                return 1
        
        payloadlen = self.in_packet.remaining_length - self.in_packet.pos
        
        payload = ""
        if payloadlen > 0:
            rc, ba_payload = self.in_packet.read_bytes(payloadlen)
            if rc != MV.ERR_SUCCESS:
                return 1
            
            payload = str(ba_payload)
        len_stripped = 10
        if payloadlen < 10 : len_stripped = payloadlen
        payload_10 = payload[:len_stripped] + "....."
        self.logger.logger.debug("Received PUBLISH from %s (t:%s,p_10:%s,q:%d,m:%d)", self.id, topic,payload_10,qos,mid)
        
        #Check for topic access
        #TODO
        
        if qos > 0:
            #TODO : save the message
            pass
        
        #send the publish-payload
        return self.send_publish_payload(mid, topic, payload, qos, retain, dup)
        
    def disconnect(self):
        if self.clean_session == 0:
            #TODO
            #store subscription. store QoS 1 and QoS 2 message
            pass
        
        self.logger.logger.info("Disconnect the Client : %s", self.id)
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
    
    def send_pingresp(self):
        self.logger.logger.debug("Sending PINGRESP to %s ", self.id)
        
        return self.send_simple_command(MV.CMD_PINGRESP)
    
    def send_publish_payload(self, mid, topic, payload, qos, retain, dup):
        if qos == 0:
            return self.send_publish_payload_qos_0(mid, topic, payload, retain, dup)
        else:
            sys.exit(-1)
            return MV.ERR_NOT_SUPPORTED
    
    def send_publish_payload_qos_0(self, mid, topic, payload, retain, dup):
        #send directly
        ls = self.sm.get_subscriber(topic)
        print "[PUBLISH]topic = ", topic, " #payload = ", payload
        rc, publish_pkt = self.build_publish_pkt(mid, topic, payload, 0, retain, dup)
        
        if len(ls) == 0:
            return MV.ERR_SUCCESS
        #return self._do_send_publish_payload(mid, topic, payload, 0, retain, dup)
        for sub in ls:
            bee = sub.bee
            bee._send_pkt(publish_pkt)
        
        return MV.ERR_SUCCESS
    
    #################################### UTIL #########################################
    def _fix_subtopic(self, topic):
        #TODO
        return MV.ERR_SUCCESS, topic
    
    def _wildcard_check(self, topic):
        #TODO
        return False