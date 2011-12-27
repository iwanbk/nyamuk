import socket
import select
import time
import sys
import logging

import base_nyamuk
import nyamuk_const as NC
from mqtt_pkt import MqttPkt
from nyamuk_msg import NyamukMsg, NyamukMsgAll
import nyamuk_net

class Nyamuk(base_nyamuk.BaseNyamuk):
    def __init__(self, id,log_level = logging.INFO):
        base_nyamuk.BaseNyamuk.__init__(self, id)
        self.in_pub_msg = []    #incoming publish message
        
        #logging
        logger = logging.Logger(id)
        
        self.logger = logging.getLogger(id)
        self.logger.setLevel(log_level)
        
        ch = logging.StreamHandler()
        ch.setLevel(log_level)
        
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        
        ch.setFormatter(formatter)
        
        self.logger.addHandler(ch)
        
    def loop(self, timeout = 1):
        rlist = [self.sock]
        wlist = []
        if len(self.out_packet) > 0:
            wlist.append(self.sock)
        
        to_read, to_write, in_error = select.select(rlist, wlist, [], timeout)
        
        if len(to_read) > 0:
            rc = self.loop_read()
            
            if rc != NC.ERR_SUCCESS:
                self.socket_close()
                if self.state == NC.CS_DISCONNECTING:
                    rc = NC.ERR_SUCCESS
                    
                if self.on_disconnect is not None:
                    self.in_callback = True
                    self.on_disconnect()
                    self.in_callback = False
                
                return rc
        
        if len(to_write) > 0:
            self.loop_write(to_write)
            
        self.loop_misc()
        
        return NC.ERR_SUCCESS
    
    def loop_read(self):
        return self.packet_read()
    
    def loop_write(self, wlist):
        return self.packet_write()
    
    def loop_misc(self):
        self.check_keepalive()
        if self.last_retry_check + 1  < time.time():
            pass
        return NC.ERR_SUCCESS
    
    def check_keepalive(self):
        if self.sock != NC.INVALID_SOCKET and time.time() - self.last_msg_out >= self.keep_alive:
            if self.state == NC.CS_CONNECTED:
                self.send_pingreq()
            else:
                self.socket_close()
    
    def packet_handle(self):
        """Incoming packet handler dispatcher."""
        cmd = self.in_packet.command & 0xF0
        
        if cmd == NC.CMD_CONNACK:
            return self.handle_connack()
        elif cmd == NC.CMD_PINGRESP:
            return self.handle_pingresp()
        elif cmd == NC.CMD_PUBLISH:
            return self.handle_publish()
        elif cmd == NC.CMD_PUBACK:
            print "Received PUBACK"
            sys.exit(-1)
        elif cmd == NC.CMD_PUBREC:
            print "Received PUBREC"
            sys.exit(-1)
        elif cmd == NC.CMD_PUBREL:
            print "Received PUBREL"
            sys.exit(-1)
        elif cmd == NC.CMD_PUBCOMP:
            print "Received PUBCOMP"
            sys.exit(-1)
        elif cmd == NC.CMD_SUBSCRIBE:
            sys.exit(-1)
        elif cmd == NC.CMD_SUBACK:
            return self.handle_suback()
        elif cmd == NC.CMD_UNSUBSCRIBE:
            print "Received UNSUBSCRIBE"
            sys.exit(-1)
        elif cmd == NC.CMD_UNSUBACK:
            print "Received UNSUBACK"
            sys.exit(-1)
        else:
            self.logger.warning("Unknown protocol. Cmd = ", cmd)
            return NC.ERR_PROTOCOL
    
    def connect(self, hostname = "localhost", port = 1883, username = None, password = None,clean_session = True):
        """Connect to server."""
        self.hostnamne = hostname
        self.port = port
        self.username = username
        self.password = password
        self.port = port
        self.clean_session = clean_session
        
        #CONNECT packet
        pkt = MqttPkt()
        pkt.connect_build(self, self.keep_alive, clean_session)
        
        #create socket
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        self.logger.info("Connecting to server ....%s",hostname)
        ret = nyamuk_net.connect(self.sock,(hostname, port))
        
        if ret != 0:
            return NC.ERR_NO_CONN
        
        #set to nonblock
        self.sock.setblocking(0)
        
        return self.packet_queue(pkt)
    
    def disconnect(self):
        self.logger.info("DISCONNECT")
        if self.sock == NC.INVALID_SOCKET:
            return NC.ERR_NO_CONN
        self.state = NC.CS_DISCONNECTING
        
        rc = self.send_disconnect()
        self.socket_close()
        return rc
    
    def subscribe(self, topic, qos):
        """Subscribe to some topic."""
        if self.sock == NC.INVALID_SOCKET:
            return NC.ERR_NO_CONN
        
        self.logger.info("SUBSCRIBE: %s", topic)
        return self.send_subscribe(False, topic, qos)
    
    def send_disconnect(self):
        return self.send_simple_command(NC.CMD_DISCONNECT)
        
    def send_subscribe(self, dup, topic, qos):
        """Send subscribe COMMAND to server."""
        pkt = MqttPkt()
        
        pktlen = 2 + 2 + len(topic) + 1
        pkt.command = NC.CMD_SUBSCRIBE | (dup << 3) | (1 << 1)
        pkt.remaining_length = pktlen
        
        rc = pkt.alloc()
        if rc != NC.ERR_SUCCESS:
            return rc
        
        #variable header
        mid = self.mid_generate()
        pkt.write_uint16(mid)
        
        #payload
        pkt.write_string(topic, len(topic))
        pkt.write_byte(qos)
        
        return self.packet_queue(pkt)
    
    def publish(self, topic, payload = None, qos = 0, retain = False):
        """Publish some payload to server."""
        #print "PUBLISHING (",topic,"): ", payload
        payloadlen = len(payload)
        if topic is None or qos < 0 or qos > 2:
            print "PUBLISH:err inval"
            return NC.ERR_INVAL
        
        if payloadlen > 268435455:
            self.logger.error("PUBLISH:err payload len:%d", payloadlen)
            return NC.ERR_PAYLOAD_SIZE
        
        #wildcard check : TODO
        
        mid = self.mid_generate()
        
        if qos == 0:
            return self.send_publish(mid, topic, payload, qos, retain, False)
        else:
            print "Unsupport QoS=", qos
        pass
    
    
    
    def handle_connack(self):
        """Handle incoming CONNACK command."""
        self.logger.info("CONNACK reveived")
        rc, byte = self.in_packet.read_byte()
        if rc != NC.ERR_SUCCESS:
            self.logger.error("error read byte")
            return rc
        
        rc, result = self.in_packet.read_byte()
        if rc != NC.ERR_SUCCESS:
            return rc
        
        if self.on_connect is not None:
            self.in_callback = True
            self.on_connect(self, result)
            self.in_callback = False
        
        if result == 0:
            self.state = NC.CS_CONNECTED
            return NC.ERR_SUCCESS
        
        elif result >= 1 and result <= 5:
            return NC.ERR_CONN_REFUSED
        else:
            return NC.ERR_PROTOCOL
    
    
    def handle_pingresp(self):
        """Handle incoming PINGRESP packet."""
        self.logger.debug("PINGRESP received")
        return NC.ERR_SUCCESS
    
    def handle_suback(self):
        """Handle incoming SUBACK packet."""
        self.logger.info("SUBACK received")
        
        rc, mid = self.in_packet.read_uint16()
        
        if rc != NC.ERR_SUCCESS:
            return rc
        
        qos_count = self.in_packet.remaining_length - self.in_packet.pos
        granted_qos = bytearray(qos_count)
        
        if granted_qos is None:
            return NC.ERR_NO_MEM
        
        i = 0
        while self.in_packet.pos < self.in_packet.remaining_length:
            rc,byte = self.in_packet.read_byte()
            
            if rc != NC.ERR_SUCCESS:
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
        
        return NC.ERR_SUCCESS
    
    def send_pingreq(self):
        """Send PINGREQ command to server."""
        self.logger.debug("SEND PINGREQ")
        self.send_simple_command(NC.CMD_PINGREQ)
    
    def handle_publish(self):
        """Handle incoming PUBLISH packet."""
        self.logger.debug("PUBLISH received")
        
        header = self.in_packet.command
        
        message = NyamukMsgAll()
        message.direction = NC.DIRECTION_IN
        message.dup = (header & 0x08) >> 3
        message.msg.qos = (header & 0x06) >> 1
        message.msg.retain = (header & 0x01)
        
        rc, ba = self.in_packet.read_string()
        message.msg.topic = ba.decode()
        
        if rc != NC.ERR_SUCCESS:
            return rc
        
        #fix_sub_topic TODO
        
        if message.msg.qos > 0:
            rc, word = self.in_packet.read_uint16()
            message.msg.mid = word
            if rc != NC.ERR_SUCCESS:
                return rc
        
        message.msg.payloadlen = self.in_packet.remaining_length - self.in_packet.pos
        
        if message.msg.payloadlen > 0:
            rc, message.msg.payload = self.in_packet.read_bytes(message.msg.payloadlen)
            if rc != NC.ERR_SUCCESS:
                return rc
        
        self.logger.debug("Received PUBLISH(dup = %d,qos=%d,retain=%s",message.dup, message.msg.qos, message.msg.retain)
        self.logger.debug("\tmid=%d, topic=%s, payloadlen=%d", message.msg.mid, message.msg.topic, message.msg.payloadlen)
        
        message.timestamp = time.time()
        
        qos = message.msg.qos
        
        if qos == 0:
            if self.on_message is not None:
                self.in_callback = True
                self.on_message(self, message.msg)
                self.in_callback = False
            else:
                self.in_pub_msg.append(message.msg)

            return NC.ERR_SUCCESS
        elif qos == 1 or qos == 2:
            self.logger.error("handle_publish. Unsupported QoS = 1 or QoS = 2")
            sys.exit(-1)
        else:
            return NC.ERR_PROTOCOL
        
        return NC.ERR_SUCCESS
    
    def send_publish(self, mid, topic, payload, qos, retain, dup):
        """Send PUBLISH."""
        self.logger.debug("Send PUBLISH")
        if self.sock == NC.INVALID_SOCKET:
            return NC.ERR_NO_CONN
        return self.send_real_publish(mid, topic, payload, qos, retain, dup)
    
    def send_real_publish(self, mid, topic, payload, qos, retain, dup):
        rc, pkt = self.build_publish_pkt(mid, topic, payload, qos, retain, dup)
        if rc != NC.ERR_SUCCESS:
            return rc
        
        return self.packet_queue(pkt)