#!/usr/bin/env python
'''
MQTT Server Based on Mosquitto
Use gevent
'''
import sys
import socket
import logging

import gevent
from gevent import monkey; monkey.patch_all()
from gevent.server import StreamServer

import subs_mgr
import conn_mgr
import bee
from MV import MV
from bee_logger import BeeLogger

SubsMgr = subs_mgr.SubscriptionManager()
ConnMgr = conn_mgr.ConnectionManager()
logger = BeeLogger(logging.DEBUG)

def handle(sock, addr):
    global SubsMgr
    global ConnMgr
    global logger
    
    print addr
    
    b = bee.Bee(sock, addr, ConnMgr, SubsMgr, logger)

    rc = b.loop(1)
    while rc == MV.ERR_SUCCESS:
        rc = b.loop()
    
    print "RC = ",rc
    
    
if __name__ == '__main__':
    bind_host = '0.0.0.0'
    bind_port = 1883
    
    server = StreamServer(('0.0.0.0', 1883),handle)
    print "Starting gevmosquittod server"
    server.serve_forever()
