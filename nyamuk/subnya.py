import sys
import nyamuk
from MV import MV

def on_connect(rc):
    print "---OnConnectCallback---"
    if rc == 0:
        print "Connected"
    else:
        print "Connect failed"
    
    print "---OnConnectCallback- end--"
        
def on_message(msg):
    print "--- message --"
    print "topic : " + msg.topic
    print "payload : " + msg.payload
    
    
def start_nyamuk(server, name, topic):
    ny = nyamuk.Nyamuk(name)
    ny.on_message = on_message
    ny.on_connect = on_connect
    
    rc = ny.connect(server)
    if rc != MV.ERR_SUCCESS:
        print "Can't connect"
        sys.exit(-1)
    
    while rc == MV.ERR_SUCCESS:
        rc = ny.loop()
    
if __name__ == '__main__':
    if len(sys.argv) != 4:
        print "cara pakai : python submq.py server name topic"
        print "contoh     : python submq.py localhost sub-iwan teknobridges"
        sys.exit(0)
        
    server = sys.argv[1]
    name = sys.argv[2]
    topic = sys.argv[3]
    start_nyamuk(server, name, topic)