'''
Nyamuk publisher example
copyright 2012 Iwan Budi Kusnanto
'''
import sys

from nyamuk import nyamuk
import nyamuk.nyamuk_const as NC
from nyamuk import event

def handle_connack(ev):
    print "CONNACK received"
    rc = ev.ret_code
    if rc == NC.CONNECT_ACCEPTED:
        print "\tconnection success"
    elif rc == 1:
        print "\tConnection refused : unacceptable protocol version"
    elif rc == 2:
        print "\tConnection refused : identifier rejected"
    elif rc == 3:
        print "\tConnection refused : broker unavailable"
    elif rc == 4:
        print "\tConnection refused : bad username or password"
    elif rc == 5:
        print "\tConnection refused : not authorized"
    else:
        print "\tConnection refused : unknown reason = ", rc
    
    return rc
    
def start_nyamuk(server, client_id, topic, payload):
    ny = nyamuk.Nyamuk(client_id, server = server)
    rc = ny.connect()
    if rc != NC.ERR_SUCCESS:
        print "Can't connect"
        sys.exit(-1)
    
    index = 0
    
    while rc == NC.ERR_SUCCESS:
        ev = ny.pop_event()
        if ev != None:
            if ev.type == NC.CMD_CONNACK:
                ret_code = handle_connack(ev)
                if ret_code == NC.CONNECT_ACCEPTED:
                    print "publishing payload"
                    ny.publish(topic, payload)
                
        rc = ny.loop()
    
if __name__ == '__main__':
    if len(sys.argv) != 5:
        print "usage   : python submq.py server name topic payload"
        print "example : python submq.py localhost sub-iwan teknobridges HaloMqtt"
        sys.exit(0)
        
    server = sys.argv[1]
    name = sys.argv[2]
    topic = sys.argv[3]
    payload = sys.argv[4]
    start_nyamuk(server, name, topic, payload)