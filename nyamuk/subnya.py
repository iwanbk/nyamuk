import sys
import nyamuk
from MV import MV

def on_connect(rc):
    if rc == 0:
        print "on_connect callback : success"
    else:
        print "on_connect callback : failed"
    
def on_message(msg):
    print "--- message --"
    print "topic : " + msg.topic
    print "payload : " + msg.payload
    
    
def start_nyamuk(server, name, topic):
    ny = nyamuk.Nyamuk(name)
    ny.on_message = on_message
    ny.on_connect = on_connect
    
    rc = ny.connect(server, keepalive = 10)
    if rc != MV.ERR_SUCCESS:
        print "Can't connect"
        sys.exit(-1)
    
    index = 0
    while rc == MV.ERR_SUCCESS:
        rc = ny.loop()
        #index += 1
        #if index == 15:
        #    sys.exit(-1)
    
if __name__ == '__main__':
    if len(sys.argv) != 4:
        print "cara pakai : python submq.py server name topic"
        print "contoh     : python submq.py localhost sub-iwan teknobridges"
        sys.exit(0)
        
    server = sys.argv[1]
    name = sys.argv[2]
    topic = sys.argv[3]
    start_nyamuk(server, name, topic)