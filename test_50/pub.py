#!/usr/bin/env python
# -*- coding: utf8 -*-
"""
    Nyamuk: simple publish example
    Copyright 2016 Guillaume Bour <guillaume@bour.cc>
"""

import sys
from nyamuk import *
from nyamuk import nyamuk_prop as props

def nloop(client):
    client.packet_write()     # flush write buffer (messages sent to MQTT server)
    client.loop()             # fill read buffer   (enqueue received messages)
    return client.pop_event() # return 1st received message (dequeued)

client = Nyamuk("test_nyamuk_pub", server="localhost")
ret = client.connect(version=5)
ret = nloop(client) # ret should be EventConnack object
if not isinstance(ret, EventConnack) or ret.ret_code != 0:
    print('connection failed'); sys.exit(1)

client.publish('foo/bar', 'this is a test', qos=1, props=[
        NyamukProp(props.PROP_PAYLOAD_FORMAT_INDICATOR, 0x01),
#        NyamukProp(props.PROP_USR_PROPERTY, (u"nyamuk", u"rocks")),
#        props.PayloadFmtIndicator(UTF8_FMT),
        props.UserProperty((u"nyamuk", u"rocks"))
    ])
ret = nloop(client) # ret should be EventPuback

client.disconnect()

