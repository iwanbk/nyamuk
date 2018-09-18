#!/usr/bin/env python
# -*- coding: utf8 -*-

import unittest
from nyamuk import *
from nyamuk import mqtt_reasons as r

class PublishTest(unittest.TestCase):
    def _packet_fire(self, c):
        c.packet_write()
        r = c.loop()

        return c.pop_event()

    def _fake_subscriber(self, topic):
        self._fake = Nyamuk("fake", server="localhost")
        ret = self._fake.connect(version=5)
        ret = self._packet_fire(self._fake)

        self._fake.subscribe(topic, qos=1)
        self._packet_fire(self._fake)

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

        if hasattr(self, '_fake') and self._fake is not None:
            self._fake.disconnect()
            self._fake.packet_write()
            self._fake = None

    # valid connect
    def test_01_valid_qos0(self):
        ret = self._c.publish("no/topic", "blabla", qos=0)
        ret = self._packet_fire(self._c)

        # we expect no response for qos 0 (fire & forget)
        self.assertEqual(ret, None)

    def test_02_valid_qos1(self):
        # init
        self._fake_subscriber("foo/bar")
        # /

        ret = self._c.publish("foo/bar", "foo/bar,qos=1", qos=1)
        ret = self._packet_fire(self._c)

        self.assertTrue(isinstance(ret, EventPuback))
        self.assertEqual(ret.reason, r.REASON_SUCCESS)


    def test_20_puback_no_matching_subscribers(self):
        ret = self._c.publish("no/topic", "blabla", qos=1)
        ret = self._packet_fire(self._c)

        # we expect no response for qos 0 (fire & forget)
        self.assertTrue(isinstance(ret, EventPuback))
        print(ret.mid, ret.reason, ret.props)
        self.assertEqual(ret.reason, r.REASON_NO_MATCH_SUBSCRIBERS)

    def test_21_puback_not_authorized(self):
        ret = self._c.publish("test_qos_1_2_errors", "blabla", qos=1)
        ret = self._packet_fire(self._c)

        # we expect no response for qos 0 (fire & forget)
        self.assertTrue(isinstance(ret, EventPuback))
        self.assertEqual(ret.reason, r.REASON_NOT_AUTHORIZED)



if __name__ == '__main__':
    unittest.main()
