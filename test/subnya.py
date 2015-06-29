'''
Nyamuk subscriber example
Copyright Iwan Budi Kusnanto
'''
import sys
import logging
import argparse

from nyamuk import nyamuk
from nyamuk import nyamuk_const as NC
from nyamuk import event

def handle_connack(ev):
    print "CONNACK received"
    rc = ev.ret_code
    if rc == 0:
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
        
def handle_publish(ev):
    msg = ev.msg
    print "PUBLISH_RECEIVED"
    print "\ttopic : " + msg.topic
    if msg.payload is not None:
        print "\tpayload : " + msg.payload

def handle_suback(ev):
    print "SUBACK RECEIVED"
    print "\tQOS Count = ", len(ev.granted_qos)
    print "\tMID = ", ev.mid
        
def start_nyamuk(server, client_id, topic, username = None, password = None):
    ny = nyamuk.Nyamuk(client_id, username, password, server)
    rc = ny.connect()
    if rc != NC.ERR_SUCCESS:
        print "Can't connect"
        sys.exit(-1)
    
    rc = ny.subscribe(topic, 0)
    
    while rc == NC.ERR_SUCCESS:
        ev = ny.pop_event()
        if ev != None:
            if ev.type == NC.CMD_CONNACK:
                handle_connack(ev)
            elif ev.type == NC.CMD_PUBLISH:
                handle_publish(ev)
            elif ev.type == NC.CMD_SUBACK:
                handle_suback(ev)
            elif ev.type == EV_NET_ERR:
                print "Network Error. Msg = ", ev.msg
                sys.exit(-1)
        rc = ny.loop()
        if rc == NC.ERR_CONN_LOST:
            ny.logger.fatal("Connection to server closed")
            
    ny.logger.info("subscriber exited")
    
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Nyamuk subscriber sample client")
    parser.add_argument('--qos', type=int, dest='qos', default=0, choices=[0, 1, 2],
        help='messages qos')
    parser.add_argument('-s', '--server', type=str, dest='server', default='localhost',
        help='mqtt server')
    parser.add_argument('-c', '--client-id', type=str, dest='client_id', required=True,
        help='client id')
    parser.add_argument('-t', '--topic', type=str, dest='topic', required=True,
        help='topic')
    args = parser.parse_args()

    start_nyamuk(args.server, args.client_id, args.topic)
