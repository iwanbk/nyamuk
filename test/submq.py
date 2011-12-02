import sys

import mosquitto

def on_connect(rc):
    if rc == 0:
        print "Connected"
    else:
        print "Connect failed"

def on_message(msg):
    print "--- message --"
    print "topic : " + msg.topic
    print "payload : " + msg.payload
    

def start_client(server, name, topic):
    c = mosquitto.Mosquitto(name)
    c.on_message = on_message
    c.on_connect = on_connect
    
    c.connect(server)
    c.subscribe(topic,2)
    
    while c.loop() == 0:
        pass
    

if __name__ == '__main__':
    if len(sys.argv) != 4:
        print "cara pakai : python submq.py server name topic"
        print "contoh     : python submq.py localhost sub-iwan teknobridges"
        sys.exit(0)
        
    server = sys.argv[1]
    name = sys.argv[2]
    topic = sys.argv[3]
    start_client(server, name, topic)