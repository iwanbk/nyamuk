#!/usr/bin/env python
# -*- coding: utf8 -*-
'''
Nyamuk publisher example
copyright 2012 Iwan Budi Kusnanto
'''
import sys
import argparse

from nyamuk import nyamuk
import nyamuk.nyamuk_const as NC
from nyamuk import event

def handle_connack(ev):
    print "CONNACK received"
    rc = ev.ret_code
    if rc == NC.CONNECT_ACCEPTED:
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

def handle_puback(ev, ny):
    print "PUBACK received (msgid={0})".format(ev.mid)
    if ev.mid != ny.get_last_mid():
        print "\tunknown msgid"

def handle_pubrec(ev, ny):
    print "PUBREC received (msgid={0})".format(ev.mid)
    if ev.mid != ny.get_last_mid():
        print "\tunknown msgid"; return False

    # send PUBREL
    ny.pubrel(ev.mid)
    return True

def handle_pubcomp(ev, ny):
    print "PUBCOMP received (msgid={0})".format(ev.mid)
    if ev.mid != ny.get_last_mid():
        print "\tunknown msgid"; return False


def start_nyamuk(server = 'localhost', port = 1883, client_id = None, topic = None, msg = None, username = None, 
                 password = None, version = 3, **kwargs):
    ny = nyamuk.Nyamuk(client_id, username, password, server=server, port=port)
    rc = ny.connect(version=version)
    if rc != NC.ERR_SUCCESS:
        print "Connection failed : can't connect to the broker"
        sys.exit(-1)

    qos = kwargs.get('qos', 0)


    while rc == NC.ERR_SUCCESS:
        rc = ny.loop()
        if rc == NC.ERR_CONN_LOST:
            ny.logger.fatal("Connection to server closed"); break

        ev = ny.pop_event()
        if ev is None:
            continue

        if ev.type == NC.CMD_CONNACK:
            ret_code = handle_connack(ev)
            if ret_code == NC.CONNECT_ACCEPTED:
                print "publishing payload"
                ny.publish(topic, msg, qos=qos)
                if qos == 0:
                    break

        # QoS = 1
        elif ev.type == NC.CMD_PUBACK:
            handle_puback(ev, ny)
            break

        # QoS = 2
        elif ev.type == NC.CMD_PUBREC:
            if not handle_pubrec(ev, ny):
                break;
        elif ev.type == NC.CMD_PUBCOMP:
            handle_pubcomp(ev, ny)
            break


    ny.disconnect()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Nyamuk subscriber sample client")
    parser.add_argument('-s', '--server', type=str, dest='server', default='localhost',
        help='mqtt server')
    parser.add_argument('-o', '--port', type=int, dest='port', default=1883,
        help='mqtt broker port')
    parser.add_argument('-c', '--client-id', type=str, dest='client_id', required=True,
        help='client id')
    parser.add_argument('-t', '--topic', type=str, dest='topic', required=True,
        help='topic')
    parser.add_argument('-m', '--message', type=str, dest='msg', required=True,
        help='message')
    parser.add_argument('-u', '--user', type=str, dest='username',
        help='username')
    parser.add_argument('-p', '--pass', type=str, dest='password',
        help='password')
    parser.add_argument('-q', '--qos', type=int, dest='qos', default=0, choices=[0, 1, 2],
        help='messages qos')
    parser.add_argument('-v', '--version', type=int, dest='version', default=3, choices=[3, 4],
        help='mqtt version')
    args = parser.parse_args()

    start_nyamuk(**vars(args))
