'''
MQTT Publisher Client
'''
import sys

from nyamuk import nyamuk
from nyamuk.MV import MV

def on_connect(nyamuk, rc):
    if rc == 0:
        print "on_connect callback : success"
    else:
        print "on_connect callback : failed"
    
def on_message(msg):
    print "--- message --"
    print "topic : " + msg.topic
    print "payload : " + msg.payload
    
    
def start_nyamuk(server, name, topic, payload):
    ny = nyamuk.Nyamuk(name)
    ny.on_message = on_message
    ny.on_connect = on_connect
    
    rc = ny.connect(server)
    if rc != MV.ERR_SUCCESS:
        print "Can't connect"
        sys.exit(-1)
    
    index = 0
    
    while rc == MV.ERR_SUCCESS:
        rc = ny.loop()
        #print "index = ", index
        index += 1
        if index == 7:
            rc = ny.publish(topic, payload)
    
if __name__ == '__main__':
    if len(sys.argv) != 5:
        print "cara pakai : python submq.py server name topic payload"
        print "contoh     : python submq.py localhost sub-iwan teknobridges HaloMqtt"
        sys.exit(0)
        
    server = sys.argv[1]
    name = sys.argv[2]
    topic = sys.argv[3]
    payload = sys.argv[4]
    start_nyamuk(server, name, topic, payload)