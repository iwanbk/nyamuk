#!/usr/bin/env python
# -*- coding: utf8 -*-

import unittest
from nyamuk import *
from nyamuk import mqtt_reasons as r

class UnsubscribeTest(unittest.TestCase):
    def _packet_fire(self, c):
        c.packet_write()
        r = c.loop()

        return c.pop_event()

    def setUp(self):
        self._c = Nyamuk("unittest", server="localhost")
        ret = self._c.connect(version=5)
        ret = self._packet_fire(self._c)

    def tearDown(self):
        if self._c is None:
            return

        #print(self._c, self._c.conn_is_alive(), self._c.sock)
        self._c.disconnect()
        # server close the connection right after receiving DISCONNECT
        self._c.packet_write()

        self._c = None

    def test_01_unsubscribe_single(self):
        ret = self._c.subscribe("simple/topic", qos=1)
        ret = self._packet_fire(self._c)
        print(ret)

        self.assertTrue(isinstance(ret, EventSuback))
        self.assertEqual(ret.reasons[0], r.REASON_GRANTED_QOS1)

        ret = self._c.unsubscribe("simple/topic")
        ret = self._packet_fire(self._c)
        print(ret)

        self.assertTrue(isinstance(ret, EventUnsuback))
        self.assertEqual(ret.reasons, [r.REASON_SUCCESS])

    def test_02_unsubscribe_multi(self):
        ret = self._c.subscribe_multi([
                ("multi/topic/0", 0, {}),
                ("multi/topic/1", 1, {}),
                ("multi/topic/#", 2, {}),
                ("multi/+/topic", 0, {}),
            ])
        ret = self._packet_fire(self._c)
        print(ret)

        self.assertTrue(isinstance(ret, EventSuback))
        self.assertEqual(ret.reasons, [0, 1, 2, 0])

        self._c.unsubscribe_multi([
                "multi/topic/0", "multi/+/topic", "multi/topic/#"
            ])
        ret = self._packet_fire(self._c)
        print(ret)

        self.assertTrue(isinstance(ret, EventUnsuback))
        self.assertEqual(ret.reasons, [0, 0, 0])

    def test_10_no_subscription_exists(self):
        ret = self._c.unsubscribe("no/topic")
        ret = self._packet_fire(self._c)
        print(ret)

        self.assertTrue(isinstance(ret, EventUnsuback))
        self.assertEqual(ret.reasons, [r.REASON_NO_SUBSCRIPTION])

if __name__ == '__main__':
    unittest.main()
