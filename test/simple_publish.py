#!/usr/bin/env python
# -*- coding: utf8 -*-
"""
    Nyamuk: simple publish example
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

client.publish('foo/bar', 'this is a test', qos=1)
ret = nloop(client) # ret should be EventPuback

client.disconnect()

