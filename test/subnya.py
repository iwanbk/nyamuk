'''
Nyamuk subscriber example
Copyright Iwan Budi Kusnanto
'''
import sys
import logging

from nyamuk import nyamuk
from nyamuk import nyamuk_const as NC

def on_connect(obj, rc):
    if rc == 0:
        print "on_connect callback : connection success"
    elif rc == 1:
        print "Connection refused : unacceptable protocol version"
    elif rc == 2:
        print "Connection refused : identifier rejected"
    elif rc == 3:
        print "Connection refused : broker unavailable"
    elif rc == 4:
        print "Connection refused : bad username or password"
    elif rc == 5:
        print "Connection refused : not authorized"
    else:
        print "Connection refused : unknown reason = ", rc
    
def on_message(nyamuk, msg):
    print "--- message --"
    print "topic : " + msg.topic
    if msg.payload is not None:
        print "payload : " + msg.payload

def on_subscribe(nyamuk, mid, granted_qos):
    print "On Subscribe"
    print "\tQOS Count = ", len(granted_qos)
    print "\tMID = ", mid
    
    
def start_nyamuk(server, name, topic):
    ny = nyamuk.Nyamuk(name, logging.DEBUG)
    ny.on_message = on_message
    ny.on_connect = on_connect
    ny.on_subscribe = on_subscribe
    #ny.keep_alive = 10 #default keepalive is 120
    
    #rc = ny.connect(server, username = "satu", password = "satu")
    rc = ny.connect(server)
    if rc != NC.ERR_SUCCESS:
        print "Can't connect"
        sys.exit(-1)
    
    rc = ny.subscribe(topic, 0)
    while rc == NC.ERR_SUCCESS:
        rc = ny.loop()
    
if __name__ == '__main__':
    if len(sys.argv) != 4:
        print "usage    : python submq.py server client_id topic"
        print "example  : python submq.py localhost sub-iwan teknobridges"
        sys.exit(0)
        
    server = sys.argv[1]
    client_id = sys.argv[2]
    topic = sys.argv[3]
    start_nyamuk(server, client_id, topic)