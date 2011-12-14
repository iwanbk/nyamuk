#!/usr/bin/env python
'''
MQTT Server Based on Mosquitto
Use gevent
'''
import sys
import socket

import gevent
from gevent import monkey; monkey.patch_socket()
from gevent.server import StreamServer

import bee
from MV import MV

def handle(sock, addr):
    print addr
    
    b = bee.Bee(sock,addr)

    rc = b.packet_read(True)
    while rc == MV.ERR_SUCCESS:
        rc = b.packet_read()
    
    
if __name__ == '__main__':
    bind_host = '0.0.0.0'
    bind_port = 1883
    
    server = StreamServer(('0.0.0.0', 1883),handle)
    print "Starting gevmosquittod server"
    server.serve_forever()
