'''
Nyamuk
Python MQTT Client Library
Copyright 2012 Iwan Budi Kusnanto <iwan.b.kusnanto@gmail.com>
'''
import time
import errno

from mqtt_pkt import MqttPkt
import nyamuk_const as NC
import nyamuk_net
import event

MQTTCONNECT = 16# 1 << 4
class BaseNyamuk:
    """Base class of nyamuk."""
    def __init__(self, client_id, username, password,
                 server, port, keepalive, ssl, ssl_opts):
        ''' Constructor '''
        self.client_id = client_id
        self.username = username
        self.password = password
        self.server = server
        self.port = port
        self.ssl = ssl
        self.ssl_opts = ssl_opts
        
        self.address = ""
        self.keep_alive = keepalive
        self.clean_session = 1
        self.state = NC.CS_NEW
        self.last_msg_in = time.time()
        self.last_msg_out = time.time()
        self.last_mid = 0
        
        #output packet queue
        self.out_packet = []
        
        #input packet queue
        self.in_packet = MqttPkt()
        self.in_packet.packet_cleanup()
        
        #networking
        self.sock = NC.INVALID_SOCKET
        
        self.will = None
        
        self.message_retry = NC.MESSAGE_RETRY
        self.last_retry_check = 0
        self.messages = None
        
        self.bridge = None
        
        #LOGGING Option:TODO
        self.log_priorities = -1
        self.log_destinations = -1
        
        self.host = None
        
        #hack var
        self.as_broker = False
        
        #event list
        self.event_list = []
        
    def pop_event(self):
        """Pop an event from event_list."""
        if len(self.event_list) > 0:
            evt = self.event_list.pop(0)
            return evt
        return None
    
    def push_event(self, evt):
        """Add an event to event_list."""
        self.event_list.append(evt)
    
    def mid_generate(self):
        """Generate mid. TODO : check."""
        self.last_mid += 1
        if self.last_mid == 0:
            self.last_mid += 1
        return self.last_mid

    def get_last_mid(self):
        return self.last_mid

    def packet_queue(self, pkt):
        """Enqueue packet to out_packet queue."""
        
        pkt.pos = 0
        pkt.to_process = pkt.packet_length
        
        self.out_packet.append(pkt)
        return NC.ERR_SUCCESS
    
    def packet_write(self):
        """Write packet to network."""
        bytes_written = 0
        
        if self.sock == NC.INVALID_SOCKET:
            return NC.ERR_NO_CONN, bytes_written
        
        while len(self.out_packet) > 0:
            pkt = self.out_packet[0]
            write_length, status = nyamuk_net.write(self.sock, pkt.payload)
            if write_length > 0:
                pkt.to_process -= write_length
                pkt.pos += write_length
                
                bytes_written += write_length
                
                if pkt.to_process > 0:
                    return NC.ERR_SUCCESS, bytes_written
            else:
                if status == errno.EAGAIN or status == errno.EWOULDBLOCK:
                    return NC.ERR_SUCCESS, bytes_written
                elif status == errno.ECONNRESET:
                    return NC.ERR_CONN_LOST, bytes_written
                else:
                    return NC.ERR_UNKNOWN, bytes_written
            
            """
            if pkt.command & 0xF6 == NC.CMD_PUBLISH and self.on_publish is not None:
                self.in_callback = True
                self.on_publish(pkt.mid)
                self.in_callback = False
            """
            
            #next
            del self.out_packet[0]
            
            #free data (unnecessary)
            
            self.last_msg_out = time.time()
            
        
        return NC.ERR_SUCCESS, bytes_written
    
    def packet_read(self):
        """Read packet from network."""
        bytes_received = 0
        
        if self.sock == NC.INVALID_SOCKET:
            return NC.ERR_NO_CONN
        
        if self.in_packet.command == 0:
            ba_data, errnum, errmsg = nyamuk_net.read(self.sock, 1)
            if errnum == 0 and len(ba_data) == 1:
                bytes_received += 1
                byte = ba_data[0]
                self.in_packet.command = byte
                
                if self.as_broker:
                    if self.bridge is None and self.state == NC.CS_NEW and (byte & 0xF0) != NC.CMD_CONNECT:
                        print "RETURN ERR_PROTOCOL"
                        return NC.ERR_PROTOCOL, bytes_received
            else:
                if errnum == errno.EAGAIN or errnum == errno.EWOULDBLOCK:
                    return NC.ERR_SUCCESS, bytes_received
                elif errnum == 0 and len(ba_data) == 0 or errnum == errno.ECONNRESET:
                    return NC.ERR_CONN_LOST, bytes_received
                else:
                    evt = event.EventNeterr(errnum, errmsg)
                    self.push_event(evt)
                    return NC.ERR_UNKNOWN, bytes_received
        
        if not self.in_packet.have_remaining:
            loop_flag = True
            while loop_flag:
                ba_data, errnum, errmsg = nyamuk_net.read(self.sock, 1)
                
                if errnum == 0 and len(ba_data) == 1:       
                    byte = ba_data[0]
                    bytes_received += 1
                    self.in_packet.remaining_count += 1
                    if self.in_packet.remaining_count > 4:
                        return NC.ERR_PROTOCOL, bytes_received
                    
                    self.in_packet.remaining_length += (byte & 127) * self.in_packet.remaining_mult
                    self.in_packet.remaining_mult *= 128
                else:
                    if errnum == errno.EAGAIN or errnum == errno.EWOULDBLOCK:
                        return NC.ERR_SUCCESS, bytes_received
                    elif errnum == 0 and len(ba_data) == 0 or errnum == errno.ECONNRESET:
                        return NC.ERR_CONN_LOST, bytes_received
                    else:
                        evt = event.EventNeterr(errnum, errmsg)
                        self.push_event(evt)
                        return NC.ERR_UNKNOWN, bytes_received
                
                if (byte & 128) == 0:
                    loop_flag = False
            
            if self.in_packet.remaining_length > 0:
                self.in_packet.payload = bytearray(self.in_packet.remaining_length)
                if self.in_packet.payload is None:
                    return NC.ERR_NO_MEM, bytes_received
                self.in_packet.to_process = self.in_packet.remaining_length
            
            self.in_packet.have_remaining = True
        
        if self.in_packet.to_process > 0:
            ba_data, errnum, errmsg = nyamuk_net.read(self.sock, self.in_packet.to_process)
            if errnum == 0 and len(ba_data) > 0:
                readlen = len(ba_data)
                bytes_received += readlen
                for idx in xrange(0, readlen):
                    self.in_packet.payload[self.in_packet.pos] = ba_data[idx]
                    self.in_packet.pos += 1
                    self.in_packet.to_process -= 1
            else:
                if errnum == errno.EAGAIN or errnum == errno.EWOULDBLOCK:
                        return NC.ERR_SUCCESS, bytes_received
                elif errnum == 0 and len(ba_data) == 0 or errnum == errno.ECONNRESET:
                    return NC.ERR_CONN_LOST, bytes_received
                else:
                    evt = event.EventNeterr(errnum, errmsg)
                    self.push_event(evt)
                    return NC.ERR_UNKNOWN, bytes_received

        #all data for this packet is read
        self.in_packet.pos = 0
        
        ret = self.packet_handle()
        
        self.in_packet.packet_cleanup()
        
        self.last_msg_in = time.time()
        
        return ret, bytes_received
                
    def socket_close(self):
        """Close our socket."""
        if self.sock != NC.INVALID_SOCKET:
            self.sock.close()
        self.sock = NC.INVALID_SOCKET

    #
    # return True is socket is connected, or False
    #
    def conn_is_alive(self):
        if self.sock == NC.INVALID_SOCKET:
            return False

        data,err,msg = nyamuk_net.read(self.sock, 1)
        if err in (errno.ECONNRESET, errno.ETIMEDOUT) :
            return False

        return True
        
    def build_publish_pkt(self, mid, topic, payload, qos, retain, dup):
        """Build PUBLISH packet."""
        pkt = MqttPkt()
        payloadlen = len(payload)
        packetlen = 2 + len(topic) + payloadlen
        
        if qos > 0:
            packetlen += 2
        
        pkt.mid = mid
        pkt.command = NC.CMD_PUBLISH | ((dup & 0x1) << 3) | (qos << 1) | retain
        pkt.remaining_length = packetlen
        
        ret = pkt.alloc()
        if ret != NC.ERR_SUCCESS:
            return ret, None
        
        #variable header : Topic String
        pkt.write_string(topic)
        
        if qos > 0:
            pkt.write_uint16(mid)
        
        #payloadlen
        if payloadlen > 0:
            pkt.write_bytes(payload, payloadlen)
        
        return NC.ERR_SUCCESS, pkt
    
    def send_simple_command(self, cmd):
        """Send simple mqtt commands."""
        pkt = MqttPkt()
        
        pkt.command = cmd
        pkt.remaining_length = 0
        
        ret = pkt.alloc()
        if ret != NC.ERR_SUCCESS:
            return ret
        
        return self.packet_queue(pkt)
