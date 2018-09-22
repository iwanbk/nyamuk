"""
Nyamuk : Python MQTT Client library
Copyright 2012 Iwan Budi Kusnanto
"""
# -*- coding: utf8 -*-

import socket
import select
import time
import sys
import ssl
import logging

import base_nyamuk
import nyamuk_const as NC
from mqtt_pkt import MqttPkt
import mqtt_types as t
from nyamuk_msg import NyamukMsgAll, NyamukMsg
import nyamuk_net
import event
from utils import utf8encode
from nyamuk_prop import *
import mqtt_reasons as r

class Nyamuk(base_nyamuk.BaseNyamuk):
    """Nyamuk mqtt client class."""
    def __init__(self, client_id, username = None, password = None,
                 server = "localhost", port = None, keepalive = NC.KEEPALIVE_VAL,
                 log_level = logging.DEBUG,
                 ssl = False, ssl_opts=[]):

        # default MQTT port
        if port is None:
            port = 8883 if ssl else 1883

        base_nyamuk.BaseNyamuk.__init__(self, client_id, username, password,
                                        server, port, keepalive, ssl, ssl_opts)

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
            return self.handle_puback()
        elif cmd == NC.CMD_PUBREC:
            return self.handle_pubrec()
        elif cmd == NC.CMD_PUBREL:
            return self.handle_pubrel()
        elif cmd == NC.CMD_PUBCOMP:
            return self.handle_pubcomp()
        elif cmd == NC.CMD_SUBSCRIBE:
            sys.exit(-1)
        elif cmd == NC.CMD_SUBACK:
            return self.handle_suback()
        elif cmd == NC.CMD_UNSUBSCRIBE:
            print "Received UNSUBSCRIBE"
            sys.exit(-1)
        elif cmd == NC.CMD_UNSUBACK:
            return self.handle_unsuback()
        elif cmd == NC.CMD_DISCONNECT:
            return self.handle_disconnect()
        else:
            self.logger.warning("Unknown protocol. Cmd = %d", cmd)
            return NC.ERR_PROTOCOL

    #
    # will = None | {'topic': Topic, 'message': Msg, 'qos': 0|1|2, retain=True|False}
    # will message, qos and retain are optional (default to empty string, 0 qos and False retain)
    #
    def connect(self, version = 3, clean_session = 1, will = None, properties = []):
        """Connect to server."""
        # NOTE: we store the version
        self.version       = version

        self.clean_session = clean_session
        self.will          = None

        if will is not None:
            self.will = NyamukMsg(
                topic = will['topic'],
                # unicode text needs to be utf8 encoded to be sent on the wire
                # str or bytearray are kept as it is
                payload = utf8encode(will.get('message','')),
                qos = will.get('qos', 0),
                retain = will.get('retain', False)
            )

        #CONNECT packet
        pkt = MqttPkt()
        pkt.connect_build(self, self.keep_alive, clean_session, version = version, props = properties)

        #create socket
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        if self.ssl:
            opts = {
                'do_handshake_on_connect': True,
                'ssl_version': ssl.PROTOCOL_TLSv1
            }
            opts.update(self.ssl_opts)
            #print opts, self.port

            try:
                self.sock = ssl.wrap_socket(self.sock, **opts)
            except Exception, e:
                self.logger.error("failed to initiate SSL connection: {0}".format(e))
                return NC.ERR_UNKNOWN

        nyamuk_net.setkeepalives(self.sock)

        self.logger.info("Connecting to server ....%s", self.server)
        err = nyamuk_net.connect(self.sock,(self.server, self.port))
        #print self.sock.cipher()

        if err != None:
            self.logger.error(err[1])
            return NC.ERR_UNKNOWN

        #set to nonblock
        self.sock.setblocking(0)

        return self.packet_queue(pkt)

    def disconnect(self, reason=0, props=[]):
        """Disconnect from server."""
        self.logger.info("DISCONNECT")
        if self.sock == NC.INVALID_SOCKET:
            return NC.ERR_NO_CONN
        self.state = NC.CS_DISCONNECTING

        ret = self.send_disconnect(reason, props)
        ret2, bytes_written = self.packet_write()

        self.socket_close()
        return ret

    def subscribe(self, topic, qos, opts={}, props=[]):
        """Subscribe to some topic.

            TODO: mqtt 5.0 - handle other topic options, and properties
        """
        if self.sock == NC.INVALID_SOCKET:
            return NC.ERR_NO_CONN

        self.logger.info("SUBSCRIBE: {0} (qos {1})".format(topic, qos))

        return self.send_subscribe([(utf8encode(topic), qos, opts)], props)

    # subscribe to multiple topic filters at once
    def subscribe_multi(self, topics, props=[]):
        """Subscribe to some topics."""
        if self.sock == NC.INVALID_SOCKET:
            return NC.ERR_NO_CONN

        self.logger.info("SUBSCRIBE: %s".format(topics))
        return self.send_subscribe(
            [(utf8encode(topic), qos, opts) for (topic, qos, opts) in topics],
            props=props)

    def unsubscribe(self, topic, props=[]):
        """Unsubscribe to some topic."""
        if self.sock == NC.INVALID_SOCKET:
            return NC.ERR_NO_CONN

        self.logger.info("UNSUBSCRIBE: %s", topic)
        return self.send_unsubscribe(props, [utf8encode(topic)])

    def unsubscribe_multi(self, topics, props=[]):
        """Unsubscribe to some topics."""
        if self.sock == NC.INVALID_SOCKET:
            return NC.ERR_NO_CONN

        self.logger.info("UNSUBSCRIBE: %s", ', '.join(topics))
        return self.send_unsubscribe(props, [utf8encode(topic) for topic in topics])

    def send_disconnect(self, reason=r.REASON_NORMAL_DISCONN, props=[]):
        """Send disconnect command."""
        pkt = MqttPkt()
        pktlen = 0

        props_len = 0
        if self.version >= 5:
            props_len += reduce(lambda x, y: x + y.len(), props, 0)
            pktlen    += t.len_varint(reason) + t.len_varint(props_len) + props_len

        pkt.command = NC.CMD_DISCONNECT
        pkt.remaining_length = pktlen

        ret = pkt.alloc()
        if ret != NC.ERR_SUCCESS:
            return ret

        # mqtt 5.0: reason code + properties
        if self.version >= 5:
            pkt.write_varint(reason)
            pkt.write_props(props, props_len)

        return self.packet_queue(pkt)

    # topics: [(topic, qos)]
    def send_subscribe(self, topics, props=[]):
        """Send subscribe COMMAND to server.

            topics is a list either
            - tuples: (topic filter, qos, nolocal, retain_as_published, retain_handling)
            - dicts: {'topic': xx, 'qos'; 1, 'nolocal': True, 'retain_as_published': True', 'retain_handling': NC.RETAIN_ALWAYS_SEND
            }
            - topic filter contains regular characters & wildcards (see section 4.7)
            - subscriber options is composed of qos value and (for mqtt 5.0) no local/retain opts

        """
        pkt = MqttPkt()

        pktlen = 2 + sum([2+len(topic)+1 for (topic, qos, opts) in topics])

        props_len = 0
        if self.version >= 5:
            props_len += reduce(lambda x, y: x + y.len(), props, 0)
            pktlen    += t.len_varint(props_len) + props_len

        pkt.command = NC.CMD_SUBSCRIBE | 0x02
        pkt.remaining_length = pktlen

        ret = pkt.alloc()
        if ret != NC.ERR_SUCCESS:
            return ret

        # variable header
        mid = self.mid_generate()
        pkt.write_uint16(mid)

        # mqtt 5.0: properties
        if self.version >= 5:
            pkt.write_props(props, props_len)

        # payload
        for (topic, qos, opts) in topics:
            pkt.write_utf8(topic)

            bitfield = qos
            if self.version >= 5:
                if opts.get('no-local', False):
                    bitfield |= 0x04
                if opts.get('retain-as-published', False):
                    bitfield |= 0x08


                print(opts.get('retain-handling', 0x00), (0x30 & opts.get('retain-handling', 0x00) << 4))
                bitfield |= (0x30 & (opts.get('retain-handling', 0x00) << 4))

            pkt.write_byte(bitfield)

        return self.packet_queue(pkt)

    def send_unsubscribe(self, props, topics):
        """Send unsubscribe COMMAND to server."""
        pkt = MqttPkt()

        # remaining length
        #   packet identifier + payload + props length
        pktlen    = 2 + sum([2+len(topic) for topic in topics])
        props_len = 0
        if self.version >= 5:
            props_len += reduce(lambda x, y: x + y.len(), props, 0)
            pktlen    += t.len_varint(props_len) + props_len

        pkt.command = NC.CMD_UNSUBSCRIBE | 0x02
        pkt.remaining_length = pktlen

        ret = pkt.alloc()
        if ret != NC.ERR_SUCCESS:
            return ret

        # variable header
        mid = self.mid_generate()
        pkt.write_uint16(mid)

        # mqtt 5.0: properties
        if self.version >= 5:
            pkt.write_props(props, props_len)

        # payload
        for topic in topics:
            pkt.write_utf8(topic)

        return self.packet_queue(pkt)

    def publish(self, topic, payload = None, qos = 0, retain = False, props=[]):
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

        if qos in (0,1,2):
            return self.send_publish(mid, topic, payload, qos, retain, False, props)

        else:
            self.logger.error("Unsupport QoS= %d", qos)

        return NC.ERR_NOT_SUPPORTED

    def handle_connack(self):
        """Handle incoming CONNACK command."""
        self.logger.info("CONNACK reveived")
        ret, flags = self.in_packet.read_byte()
        if ret != NC.ERR_SUCCESS:
            self.logger.error("error read byte")
            return ret

        # useful for >= v3.1.1 only
        session_present = flags & 0x01


        # NOTE: in v5, "return code" is renamed "reason code"
        ret, reason = self.in_packet.read_byte()
        if ret != NC.ERR_SUCCESS:
            return ret

        # mqtt 5.0: properties
        props = []
        if self.version >= 5:
            ret, props = self.in_packet.read_props()

            # if CONNACK contains KeepAlive property, we must use that value as keepalive
            ka = filter(lambda x: isinstance(x, ServerKeepAlive), props)
            if len(ka) > 0:
                self.keep_alive = ka[0].value

        evt = event.EventConnack(reason, session_present, props=props)
        self.push_event(evt)

        if reason == NC.CONNECT_ACCEPTED:
            self.state = NC.CS_CONNECTED
            return NC.ERR_SUCCESS

        # mqtt < 5.0 reason code is always < 6
        # mqtt 5.0 reason code is 0 or >= 128
        elif reason >= 1 and reason <= 5:
            return NC.ERR_CONN_REFUSED
        else:
            return NC.ERR_PROTOCOL

    def handle_pingresp(self):
        """Handle incoming PINGRESP packet."""
        self.logger.debug("PINGRESP received")
        self.push_event(event.EventPingResp())
        return NC.ERR_SUCCESS

    def handle_suback(self):
        """Handle incoming SUBACK packet."""
        self.logger.info("SUBACK received")

        ret, mid = self.in_packet.read_uint16()

        if ret != NC.ERR_SUCCESS:
            return ret

        # mqtt 5.0: properties
        props = []
        if self.version >= 5:
            ret, props = self.in_packet.read_props()

        # payload
        # NOTE: in mqtt 5.0, the payload is generalized to contains either
        payload_size = self.in_packet.remaining_length - self.in_packet.pos
        reasons      = bytearray(payload_size)

        if reasons is None:
            return NC.ERR_NO_MEM

        for i in range(payload_size):
            ret, byte = self.in_packet.read_byte()

            if ret != NC.ERR_SUCCESS:
                return ret

            reasons[i] = byte

        evt = event.EventSuback(mid, list(reasons), props=props)
        self.push_event(evt)

        granted_qos = None

        return NC.ERR_SUCCESS

    def handle_unsuback(self):
        """Handle incoming UNSUBACK packet."""
        self.logger.info("UNSUBACK received")

        ret, mid = self.in_packet.read_uint16()

        if ret != NC.ERR_SUCCESS:
            return ret

        # mqtt 5.0: properties
        props = []
        if self.version >= 5:
            ret, props = self.in_packet.read_props()

        evt = event.EventUnsuback(mid, props)
        self.push_event(evt)

        return NC.ERR_SUCCESS

    def send_pingreq(self):
        """Send PINGREQ command to server."""
        self.logger.debug("SEND PINGREQ")
        return self.send_simple_command(NC.CMD_PINGREQ)

    def handle_publish(self):
        """Handle incoming PUBLISH packet."""
        self.logger.debug("PUBLISH received")

        header = self.in_packet.command

        message = NyamukMsgAll()
        message.direction = NC.DIRECTION_IN
        message.dup = (header & 0x08) >> 3
        message.msg.qos = (header & 0x06) >> 1
        message.msg.retain = (header & 0x01)

        ret, ba_data = self.in_packet.read_utf8()
        message.msg.topic = ba_data.decode('utf8')

        if ret != NC.ERR_SUCCESS:
            return ret

        #fix_sub_topic TODO
        if message.msg.qos > 0:
            ret, word = self.in_packet.read_uint16()
            message.msg.mid = word
            if ret != NC.ERR_SUCCESS:
                return ret

        # mqtt 5.0: properties
        props = []
        if self.version >= 5:
            ret, props = self.in_packet.read_props()

        # payload
        message.msg.payloadlen = self.in_packet.remaining_length - self.in_packet.pos

        if message.msg.payloadlen > 0:
            ret, message.msg.payload = self.in_packet.read_bytes(message.msg.payloadlen)
            if ret != NC.ERR_SUCCESS:
                return ret

        self.logger.debug("Received PUBLISH(dup = %d,qos=%d,retain=%s", message.dup, message.msg.qos, message.msg.retain)
        self.logger.debug("\tmid=%d, topic=%s, payloadlen=%d", message.msg.mid, message.msg.topic, message.msg.payloadlen)

        message.timestamp = time.time()

        qos = message.msg.qos

        if qos in (0,1,2):
            evt = event.EventPublish(message.msg, props=props)
            self.push_event(evt)

            return NC.ERR_SUCCESS

        else:
            return NC.ERR_PROTOCOL

        return NC.ERR_SUCCESS

    def send_publish(self, mid, topic, payload, qos, retain, dup, props=[]):
        """Send PUBLISH."""
        self.logger.debug("Send PUBLISH")
        if self.sock == NC.INVALID_SOCKET:
            return NC.ERR_NO_CONN

        #NOTE: payload may be any kind of data
        #      yet if it is a unicode string we utf8-encode it as convenience
        return self._do_send_publish(mid, utf8encode(topic), utf8encode(payload), qos, retain, dup,
            props)

    def _do_send_publish(self, mid, topic, payload, qos, retain, dup, props=[]):
        ret, pkt = self.build_publish_pkt(mid, topic, payload, qos, retain, dup, props)
        if ret != NC.ERR_SUCCESS:
            return ret

        return self.packet_queue(pkt)

    def handle_puback(self):
        """Handle incoming PUBACK packet."""
        self.logger.info("PUBACK received")

        ret, mid = self.in_packet.read_uint16()
        reason = 0x00 # SUCCESS
        props  = []
        #NOTE: reason is optional (#3.4.2.1)
        if self.version >= 5 and self.in_packet.remaining_length > 2:
            ret, reason = self.in_packet.read_byte()

            #NOTE: properties are optional (#3.4.2.2.1)
            if self.in_packet.remaining_length >= 4:
                ret, props  = self.in_packet.read_props()

        if ret != NC.ERR_SUCCESS:
            return ret

        evt = event.EventPuback(mid, reason=reason, props=props)
        self.push_event(evt)

        return NC.ERR_SUCCESS

    def handle_pubrec(self):
        """Handle incoming PUBREC packet."""
        self.logger.info("PUBREC received")

        ret, mid = self.in_packet.read_uint16()

        if ret != NC.ERR_SUCCESS:
            return ret

        evt = event.EventPubrec(mid)
        self.push_event(evt)

        return NC.ERR_SUCCESS

    def handle_pubrel(self):
        """Handle incoming PUBREL packet."""
        self.logger.info("PUBREL received")

        ret, mid = self.in_packet.read_uint16()

        if ret != NC.ERR_SUCCESS:
            return ret

        evt = event.EventPubrel(mid)
        self.push_event(evt)

        return NC.ERR_SUCCESS

    def handle_pubcomp(self):
        """Handle incoming PUBCOMP packet."""
        self.logger.info("PUBCOMP received")

        ret, mid = self.in_packet.read_uint16()

        if ret != NC.ERR_SUCCESS:
            return ret

        evt = event.EventPubcomp(mid)
        self.push_event(evt)

        return NC.ERR_SUCCESS

    def handle_disconnect(self):
        """Handle incoming DISCONNECT packet."""
        self.logger.info("DISCONNECT received")

        reason = r.REASON_NORMAL_DISCONN
        props  = []
        # mqtt 5.0: reason is optional (default NORMAL_DISCONNECT)
        if self.version and self.in_packet.remaining_length > 0:
            ret, reason = self.in_packet.read_byte()

            if self.in_packet.remaining_length > 1:
                ret, props  = self.in_packet.read_props()

        if ret != NC.ERR_SUCCESS:
            return ret

        evt = event.EventDisconnect(reason, props=props)
        self.push_event(evt)

        return NC.ERR_SUCCESS

    def puback(self, mid, reason=r.REASON_SUCCESS, props=[]):
        """Send PUBACK response to server."""
        if self.sock == NC.INVALID_SOCKET:
            return NC.ERR_NO_CONN

        self.logger.info("Send PUBACK (msgid=%s)", mid)
        pkt = MqttPkt()

        pkt.command = NC.CMD_PUBACK
        pkt.remaining_length = 2
        # mqtt 5.0
        props_len = 0
        if self.version >= 5:
            props_len += reduce(lambda x, y: x + y.len(), props, 0)

            # reason code + properties length + properties
            pkt.remaining_length += 1
            # NOTE: according to specs (3.4.2.2.1) properties length field is optional
            #       if there's no properties
            #       but to remain compliant with bad server implementation, we add it anyway
            pkt.remaining_length += t.len_varint(props_len) + props_len

        ret = pkt.alloc()
        if ret != NC.ERR_SUCCESS:
            return ret

        #variable header: acknowledged message id
        pkt.write_uint16(mid)

        if self.version >= 5:
            pkt.write_byte(reason)
            pkt.write_props(props, props_len)

        return self.packet_queue(pkt)

    def pubrel(self, mid):
        """Send PUBREL response to server."""
        if self.sock == NC.INVALID_SOCKET:
            return NC.ERR_NO_CONN

        self.logger.info("Send PUBREL (msgid=%s)", mid)
        pkt = MqttPkt()

        # PUBREL QOS = 1
        pkt.command = NC.CMD_PUBREL | (1 << 1)
        pkt.remaining_length = 2

        ret = pkt.alloc()
        if ret != NC.ERR_SUCCESS:
            return ret

        #variable header: acknowledged message id
        pkt.write_uint16(mid)

        return self.packet_queue(pkt)

    def pubrec(self, mid):
        """Send PUBREC response to server."""
        if self.sock == NC.INVALID_SOCKET:
            return NC.ERR_NO_CONN

        self.logger.info("Send PUBREC (msgid=%s)", mid)
        pkt = MqttPkt()

        pkt.command = NC.CMD_PUBREC
        pkt.remaining_length = 2

        ret = pkt.alloc()
        if ret != NC.ERR_SUCCESS:
            return ret

        #variable header: acknowledged message id
        pkt.write_uint16(mid)

        return self.packet_queue(pkt)

    def pubcomp(self, mid):
        """Send PUBCOMP response to server."""
        if self.sock == NC.INVALID_SOCKET:
            return NC.ERR_NO_CONN

        self.logger.info("Send PUBCOMP (msgid=%s)", mid)
        pkt = MqttPkt()

        pkt.command = NC.CMD_PUBCOMP
        pkt.remaining_length = 2

        ret = pkt.alloc()
        if ret != NC.ERR_SUCCESS:
            return ret

        #variable header: acknowledged message id
        pkt.write_uint16(mid)

        return self.packet_queue(pkt)

    """ destructor """
    def __del__(self):
        self.logger.handlers=[]
