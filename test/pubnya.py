'''
Nyamuk publisher example
copyright 2012 Iwan Budi Kusnanto
'''
import sys
import argparse

from nyamuk import nyamuk
import nyamuk.nyamuk_const as NC
from nyamuk import event

def handle_connack(ev):
    print "CONNACK received"
    rc = ev.ret_code
    if rc == NC.CONNECT_ACCEPTED:
        print "\tconnection successful"
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
    
def start_nyamuk(server, client_id, topic, payload, username = None, password = None):
    ny = nyamuk.Nyamuk(client_id, username, password, server)
    rc = ny.connect()
    if rc != NC.ERR_SUCCESS:
        print "Connection failed : can't connect to the broker"
        sys.exit(-1)
    
    while rc == NC.ERR_SUCCESS:
        rc = ny.loop()
        if rc == NC.ERR_CONN_LOST:
            ny.logger.fatal("Connection to server closed"); break

        ev = ny.pop_event()
        if ev is None:
            continue

        if ev.type == NC.CMD_CONNACK:
            ret_code = handle_connack(ev)
            if ret_code == NC.CONNECT_ACCEPTED:
                print "publishing payload"
                ny.publish(topic, payload)
                break

    ny.disconnect()


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
    parser.add_argument('-m', '--message', type=str, dest='msg', required=True,
        help='message')
    parser.add_argument('-u', '--user', type=str, dest='username',
        help='username')
    parser.add_argument('-p', '--pass', type=str, dest='password',
        help='password')
    args = parser.parse_args()

    start_nyamuk(args.server, args.client_id, args.topic, args.msg, args.username, args.password)
