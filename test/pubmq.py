import mosquitto
import sys

def on_connect(rc):
    if rc == 0:
        print "Connected"
    else:
        print "Connect failed"

def on_publish(obj,mid):
    print "message ", mid, "published"
    obj.disconnect()
    

def on_disconnect():
    print "disconnected successfully"

def publish_msg(server, name, topic, msg):
    c = mosquitto.Mosquitto(name)
    c.on_connect = on_connect
    c.on_publish = on_publish
    c.on_disconnect = on_disconnect
    
    c.connect(server)
    
    c.publish(topic,msg, 2)
    
    while c.loop() == 0:
        pass

if __name__ == '__main__':
    if len(sys.argv) != 5:
        print "cara pakai : python pubmq.py server nama_client topic message"
        print "contoh     : python pubmq.py 127.0.0.1 pub-ibk teknobridges hahahahah"
        sys.exit(0)
        
    publish_msg(sys.argv[1],sys.argv[2], sys.argv[3], sys.argv[4])