#!/usr/bin/env python
# -*- coding: utf8 -*-
"""
    Nyamuk: simple subscribe example
    Copyright 2016 Guillaume Bour <guillaume@bour.cc>
"""

import sys
from nyamuk import *
from nyamuk import mqtt_types
from nyamuk.nyamuk_prop import *

def nloop(client):
    client.packet_write()     # flush write buffer (messages sent to MQTT server)
    ret = client.loop()       # fill read buffer   (enqueue received messages)
    if ret != NC.ERR_SUCCESS:
        return ret, None

    return NC.ERR_SUCCESS, client.pop_event() # return 1st received message (dequeued)

client = Nyamuk("test_nyamuk", server="localhost")
ret = client.connect(version=5, properties=[
        UserProperty((u"chou",u"pette"))
    ])

ret, evt = nloop(client) # ret should be EventConnack object
if ret != NC.ERR_SUCCESS or not isinstance(evt, EventConnack) or evt.ret_code != 0:
    print('connection failed:', ret, evt); sys.exit(1)

# QoS 1
client.subscribe('foo/bar', qos=1, props=[
        SubscriptionIdentifier(42)
    ])
ret, evt = nloop(client)
if ret != NC.ERR_SUCCESS or not isinstance(evt, EventSuback):
    print('SUBACK not received:', ret, evt); sys.exit(2)
print('granted qos is {0} for "foo/bar" topic'.format(evt.granted_qos[0]))


# reception loop
try:
    while True:
        ret, evt = nloop(client)
        if ret != NC.ERR_SUCCESS:
            print('smth goes wrong, exiting', ret); sys.exit(1)

        if isinstance(evt, EventPublish):
            print('we received a message: {0} (topic= {1})'.format(evt.msg.payload, evt.msg.topic))
            if len(evt.props) > 0:
                print(" properties:")
                for p in evt.props:
                    print("  {0} = {1}".format(get_property_description(p.id), p.value))

            # received message is either qos 0 or 1
            # in case of qos 1, we must send back PUBACK message with same packet-id
            if evt.msg.qos == 1:
                client.puback(evt.msg.mid)

except KeyboardInterrupt:
    pass

client.disconnect()
