import sys
import logging

from nyamuk import nyamuk
from nyamuk import nyamuk_const as NC

the_topic = ""
def on_connect(obj, rc):
    if rc == 0:
        print "on_connect callback : connection success"
        #print "subscribing to topic = ", the_topic
        #mid = 1
        #rc = obj.subscribe(mid, topic, 0)
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
    
def make_sha(password):
    import hashlib
    
    m = hashlib.sha1(password)
    return m.hexdigest()
    
def start_nyamuk(server, topic, name, username, password):
    ny = nyamuk.Nyamuk(name, logging.DEBUG)
    ny.on_message = on_message
    ny.on_connect = on_connect
    ny.on_subscribe = on_subscribe
    ny.keep_alive = 10
    the_topic = topic
    
    #rc = ny.connect(server, username = "satu", password = "satu")
    #rc = ny.connect(server)
    rc = ny.connect(server, username = username, password = make_sha(password))
    if rc != NC.ERR_SUCCESS:
        print "Can't connect"
        sys.exit(-1)
    
    index = 0
    while rc == NC.ERR_SUCCESS:
        rc = ny.loop()
        index += 1
        if index == 3:
            rc = ny.subscribe(topic, 0)
    
if __name__ == '__main__':
    print "len sys argv = ", len(sys.argv)
    if len(sys.argv) != 6:
        print "cara pakai : python pass-sub.py server topic name user pass"
        print "contoh     : python pass-sub.py localhost tekno paijo paijo paijo"
        sys.exit(0)
        
    server = sys.argv[1]
    topic = sys.argv[2]
    name = sys.argv[3]
    username = sys.argv[4]
    password = sys.argv[5]
    the_topic = topic
    start_nyamuk(server, topic, name, username, password)