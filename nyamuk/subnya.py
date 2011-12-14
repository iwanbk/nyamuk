import sys
import nyamuk
from MV import MV

the_topic = ""
def on_connect(rc, obj):
    if rc == 0:
        print "on_connect callback : success"
        #print "subscribing to topic = ", the_topic
        #mid = 1
        #rc = obj.subscribe(mid, topic, 0)
    else:
        print "on_connect callback : failed"
    
def on_message(nyamuk, msg):
    print "--- message --"
    print "topic : " + msg.topic
    print "payload : " + msg.payload

def on_subscribe(nyamuk, mid, granted_qos):
    print "On Subscribe"
    print "\tQOS Count = ", len(granted_qos)
    print "\tMID = ", mid
    
    
def start_nyamuk(server, name, topic):
    ny = nyamuk.Nyamuk(name)
    ny.on_message = on_message
    ny.on_connect = on_connect
    ny.on_subscribe = on_subscribe
    the_topic = topic
    
    rc = ny.connect(server)
    if rc != MV.ERR_SUCCESS:
        print "Can't connect"
        sys.exit(-1)
    
    index = 0
    while rc == MV.ERR_SUCCESS:
        print "index = ", index
        rc = ny.loop()
        index += 1
        if index == 5:
            mid = 0
            rc = ny.subscribe(mid, topic, 0)
    
if __name__ == '__main__':
    if len(sys.argv) != 4:
        print "cara pakai : python submq.py server name topic"
        print "contoh     : python submq.py localhost sub-iwan teknobridges"
        sys.exit(0)
        
    server = sys.argv[1]
    name = sys.argv[2]
    topic = sys.argv[3]
    the_topic = topic
    start_nyamuk(server, name, topic)