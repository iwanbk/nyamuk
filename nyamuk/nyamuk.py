"""
Nyamuk : Python MQTT Client library
Copyright 2012 Iwan Budi Kusnanto
"""
import socket
import select
import time
import sys
import logging

import base_nyamuk
import nyamuk_const as NC
from mqtt_pkt import MqttPkt
from nyamuk_msg import NyamukMsgAll
import nyamuk_net
import event

class Nyamuk(base_nyamuk.BaseNyamuk):
    """Nyamuk mqtt client class."""
    def __init__(self, client_id, username = None, password = None,
                 server = "localhost", port = 1883, keepalive = NC.KEEPALIVE_VAL,
                 log_level = logging.DEBUG):
        base_nyamuk.BaseNyamuk.__init__(self, client_id, username, password,
                                        server, port, keepalive)
        
        #logging
        self.logger = logging.getLogger(client_id)
        self.logger.setLevel(log_level)
        
        ch = logging.StreamHandler()
        ch.setLevel(log_level)
        
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        
        ch.setFormatter(formatter)
        
        self.logger.addHandler(ch)
        
    def loop(self, timeout = 1):
        """Main loop."""
        rlist = [self.sock]
        wlist = []
        if len(self.out_packet) > 0:
            wlist.append(self.sock)
        
        to_read, to_write, _ = select.select(rlist, wlist, [], timeout)
        
        if len(to_read) > 0:
            ret, _ = self.loop_read()
            if ret != NC.ERR_SUCCESS:
                return ret
        
        if len(to_write) > 0:
            ret, _ = self.loop_write()
            if ret != NC.ERR_SUCCESS:
                return ret
            
        self.loop_misc()
        
        return NC.ERR_SUCCESS
    
    def loop_read(self):
        """Read loop."""
        ret, bytes_received = self.packet_read()
        return ret, bytes_received
    
    def loop_write(self):
        """Write loop."""
        ret, bytes_written =  self.packet_write()
        return ret, bytes_written
    
    def loop_misc(self):
        """Misc loop."""
        self.check_keepalive()
        if self.last_retry_check + 1  < time.time():
            pass
        return NC.ERR_SUCCESS
    
    def check_keepalive(self):
        """Send keepalive/PING if necessary."""
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
            self.logger.warning("Unknown protocol. Cmd = %d", cmd)
            return NC.ERR_PROTOCOL
    
    def connect(self, clean_session = 1):
        """Connect to server."""
        self.clean_session = clean_session
        
        #CONNECT packet
        pkt = MqttPkt()
        pkt.connect_build(self, self.keep_alive, clean_session)
        
        #create socket
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        nyamuk_net.setkeepalives(self.sock)
        
        self.logger.info("Connecting to server ....%s", self.server)
        err = nyamuk_net.connect(self.sock,(self.server, self.port))
        
        if err != None:
            self.logger.error(err[1])
            return NC.ERR_UNKNOWN
        
        #set to nonblock
        self.sock.setblocking(0)
        
        return self.packet_queue(pkt)
    
    def disconnect(self):
        """Disconnect from server."""
        self.logger.info("DISCONNECT")
        if self.sock == NC.INVALID_SOCKET:
            return NC.ERR_NO_CONN
        self.state = NC.CS_DISCONNECTING
        
        ret = self.send_disconnect()
        self.socket_close()
        return ret
    
    def subscribe(self, topic, qos):
        """Subscribe to some topic."""
        if self.sock == NC.INVALID_SOCKET:
            return NC.ERR_NO_CONN
        
        self.logger.info("SUBSCRIBE: %s", topic)
        return self.send_subscribe(False, topic, qos)
    
    def send_disconnect(self):
        """Send disconnect command."""
        return self.send_simple_command(NC.CMD_DISCONNECT)
        
    def send_subscribe(self, dup, topic, qos):
        """Send subscribe COMMAND to server."""
        pkt = MqttPkt()
        
        pktlen = 2 + 2 + len(topic) + 1
        pkt.command = NC.CMD_SUBSCRIBE | (dup << 3) | (1 << 1)
        pkt.remaining_length = pktlen
        
        ret = pkt.alloc()
        if ret != NC.ERR_SUCCESS:
            return ret
        
        #variable header
        mid = self.mid_generate()
        pkt.write_uint16(mid)
        
        #payload
        pkt.write_string(topic)
        pkt.write_byte(qos)
        
        return self.packet_queue(pkt)
    
    def publish(self, topic, payload = None, qos = 0, retain = False):
        """Publish some payload to server."""
        #print "PUBLISHING (",topic,"): ", payload
        payloadlen = len(payload)
        if topic is None or qos < 0 or qos > 2:
            print "PUBLISH:err inval"
            return NC.ERR_INVAL
        
        #payloadlen <= 250MB
        if payloadlen > (250 * 1024 * 1204):
            self.logger.error("PUBLISH:err payload len:%d", payloadlen)
            return NC.ERR_PAYLOAD_SIZE
        
        #wildcard check : TODO
        mid = self.mid_generate()
        
        if qos == 0:
            return self.send_publish(mid, topic, payload, qos, retain, False)
        else:
            self.logger.error("Unsupport QoS=", qos)
    
    def handle_connack(self):
        """Handle incoming CONNACK command."""
        self.logger.info("CONNACK reveived")
        ret, _ = self.in_packet.read_byte()
        if ret != NC.ERR_SUCCESS:
            self.logger.error("error read byte")
            return ret
        
        ret, result = self.in_packet.read_byte()
        if ret != NC.ERR_SUCCESS:
            return ret
        
        evt = event.EventConnack(ret)
        self.push_event(evt)
        
        if result == NC.CONNECT_ACCEPTED:
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
        
        ret, mid = self.in_packet.read_uint16()
        
        if ret != NC.ERR_SUCCESS:
            return ret
        
        qos_count = self.in_packet.remaining_length - self.in_packet.pos
        granted_qos = bytearray(qos_count)
        
        if granted_qos is None:
            return NC.ERR_NO_MEM
        
        i = 0
        while self.in_packet.pos < self.in_packet.remaining_length:
            ret, byte = self.in_packet.read_byte()
            
            if ret != NC.ERR_SUCCESS:
                granted_qos = None
                return ret
            
            granted_qos[i] = byte
            
            i += 1
        
        evt = event.EventSuback(mid, granted_qos)
        self.push_event(evt)
        
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
        
        ret, ba_data = self.in_packet.read_string()
        message.msg.topic = ba_data.decode()
        
        if ret != NC.ERR_SUCCESS:
            return ret
        
        #fix_sub_topic TODO
        if message.msg.qos > 0:
            ret, word = self.in_packet.read_uint16()
            message.msg.mid = word
            if ret != NC.ERR_SUCCESS:
                return ret
        
        message.msg.payloadlen = self.in_packet.remaining_length - self.in_packet.pos
        
        if message.msg.payloadlen > 0:
            ret, message.msg.payload = self.in_packet.read_bytes(message.msg.payloadlen)
            if ret != NC.ERR_SUCCESS:
                return ret
        
        self.logger.debug("Received PUBLISH(dup = %d,qos=%d,retain=%s", message.dup, message.msg.qos, message.msg.retain)
        self.logger.debug("\tmid=%d, topic=%s, payloadlen=%d", message.msg.mid, message.msg.topic, message.msg.payloadlen)
        
        message.timestamp = time.time()
        
        qos = message.msg.qos
        
        if qos == 0:
            evt = event.EventPublish(message.msg)
            self.push_event(evt)

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
        return self._do_send_publish(mid, topic, payload, qos, retain, dup)
    
    def _do_send_publish(self, mid, topic, payload, qos, retain, dup):
        ret, pkt = self.build_publish_pkt(mid, topic, payload, qos, retain, dup)
        if ret != NC.ERR_SUCCESS:
            return ret
        
        return self.packet_queue(pkt)