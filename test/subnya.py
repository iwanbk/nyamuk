#!/usr/bin/env python
# -*- coding: utf8 -*-
'''
Nyamuk subscriber example
Copyright Iwan Budi Kusnanto
'''
import sys
import logging
import argparse

from nyamuk import nyamuk
from nyamuk import nyamuk_const as NC
from nyamuk import event

def handle_connack(ev):
    print "CONNACK received"
    rc = ev.ret_code
    if rc == 0:
        print "\tconnection successful"
    elif rc == 1:
        print "\tConnection refused : unacceptable protocol version"
    elif rc == 2:
        print "\tConnection refused : identifier rejected"
    elif rc == 3:
        print "\tConnection refused : broker unavailable"
    elif rc == 4:
        print "\tConnection refused : bad username or password"
    elif rc == 5:
        print "\tConnection refused : not authorized"
    else:
        print "\tConnection refused : unknown reason = ", rc

    return rc

def handle_publish(ev, ny):
    msg = ev.msg
    print "PUBLISH_RECEIVED"
    print "\ttopic : " + msg.topic
    if msg.payload is not None:
        print "\tpayload : " + msg.payload

    if msg.qos == 1:
        ny.puback(msg.mid)
    elif msg.qos == 2:
        ny.pubrec(msg.mid)

def handle_suback(ev, ny):
    print "SUBACK RECEIVED"
    print "\tQOS Count = ", len(ev.granted_qos)
    print "\tMID = ", ev.mid

def handle_pubrel(ev, ny):
    print "PUBREL RECEIVED (msgid= {0})".format(ev.mid)
    ny.pubcomp(ev.mid)


def start_nyamuk(server = 'localhost', port = 1883, client_id = None, topic = None, username = None, 
                 password = None, version = 3, **kwargs):
    ny = nyamuk.Nyamuk(client_id, username, password, server=server, port=port)
    rc = ny.connect(version=version)
    if rc != NC.ERR_SUCCESS:
        print "Connection failed : can't connect to the broker"
        sys.exit(-1)

    # queued after CONNECT
    rc = ny.subscribe(topic, kwargs.get('qos',0))

    while rc == NC.ERR_SUCCESS:
        rc = ny.loop()
        if rc == NC.ERR_CONN_LOST:
            ny.logger.fatal("Connection to server closed"); break

        ev = ny.pop_event()
        if ev is None:
            continue

        if ev.type == NC.CMD_CONNACK:
            handle_connack(ev)
        elif ev.type == NC.CMD_PUBLISH:
            handle_publish(ev, ny)
        elif ev.type == NC.CMD_SUBACK:
            handle_suback(ev, ny)
        elif ev.type == NC.CMD_PUBREL:
            handle_pubrel(ev, ny)

        elif ev.type == event.EV_NET_ERR:
            print "Network Error. Msg = ", ev.msg
            sys.exit(-1)

    ny.logger.info("subscriber exited")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Nyamuk subscriber sample client")
    parser.add_argument('-s', '--server', type=str, dest='server', default='localhost',
        help='mqtt broker address')
    parser.add_argument('-o', '--port', type=int, dest='port', default=1883,
        help='mqtt broker port')
    parser.add_argument('-c', '--client-id', type=str, dest='client_id', required=True,
        help='client id')
    parser.add_argument('-t', '--topic', type=str, dest='topic', required=True,
        help='topic')
    parser.add_argument('-u', '--user', type=str, dest='username',
        help='username')
    parser.add_argument('-p', '--pass', type=str, dest='password',
        help='password')
    parser.add_argument('--qos', type=int, dest='qos', default=0, choices=[0, 1, 2],
        help='messages qos')
    parser.add_argument('-v', '--version', type=int, dest='version', default=3, choices=[3, 4],
        help='mqtt version')
    args = parser.parse_args()

    start_nyamuk(**vars(args))
