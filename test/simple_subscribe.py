#!/usr/bin/env python
# -*- coding: utf8 -*-
"""
    Nyamuk: simple subscribe example
    Copyright 2016 Guillaume Bour <guillaume@bour.cc>
"""

import sys
from nyamuk import *

def nloop(client):
    client.packet_write()     # flush write buffer (messages sent to MQTT server)
    client.loop()             # fill read buffer   (enqueue received messages)
    return client.pop_event() # return 1st received message (dequeued)

client = Nyamuk("test_nyamuk", server="test.mosquitto.org")
ret = client.connect(version=4)
ret = nloop(client) # ret should be EventConnack object
if not isinstance(ret, EventConnack) or ret.ret_code != 0:
    print 'connection failed'; sys.exit(1)

client.subscribe('foo/bar', qos=1)
ret = nloop(client)
if not isinstance(ret, EventSuback):
    print 'SUBACK not received'; sys.exit(2)
print 'granted qos is', ret.granted_qos[0]

try:
    while True:
        evt = nloop(client)
        if isinstance(evt, EventPublish):
            print 'we received a message: {0} (topic= {1})'.format(evt.msg.payload, evt.msg.topic)
            
            # received message is either qos 0 or 1
            # in case of qos 1, we must send back PUBACK message with same packet-id
            if evt.msg.qos == 1:
                client.puback(evt.msg.mid)

except KeyboardInterrupt:
    pass

client.disconnect()
