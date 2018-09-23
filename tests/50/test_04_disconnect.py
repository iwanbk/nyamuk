#!/usr/bin/env python
# -*- coding: utf8 -*-

import unittest
from nyamuk import *
from nyamuk import mqtt_reasons as r

class DisconnectTest(unittest.TestCase):
    def _packet_fire(self, c):
        c.packet_write()
        r = c.loop()

        return c.pop_event()

    def test_01_regular_disconnect(self):
        c = Nyamuk("unittest", server="localhost")
        ret = c.connect(version=5)
        ret = self._packet_fire(c)

        ret = c.disconnect()
        print(ret)

        self.assertFalse(c.conn_is_alive())

    def test_02_disconnect_on_error(self):
        c = Nyamuk("unittest", server="localhost")
        ret = c.connect(version=5)
        ret = self._packet_fire(c)

        # NOTE: 'cmd/disconnectWithRC' topic is a special one for paho.mqtt.tests broker
        #       it triggers a forced disconnection from the broker
        c.publish("cmd/disconnectWithRC", r.get_reason_name(r.REASON_SERVER_SHUTTING_DOWN), qos=0)
        ret = self._packet_fire(c)
        print(ret)

        self.assertTrue(isinstance(ret, EventDisconnect))
        self.assertEqual(ret.reason, r.REASON_SERVER_SHUTTING_DOWN)
        self.assertFalse(c.conn_is_alive())

if __name__ == '__main__':
    unittest.main()
