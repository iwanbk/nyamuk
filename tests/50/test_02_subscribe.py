#!/usr/bin/env python
# -*- coding: utf8 -*-

import unittest
from nyamuk import *
from nyamuk import mqtt_reasons as r

class SubscribeTest(unittest.TestCase):
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

    def test_01_subscribe_qos0(self):
        ret = self._c.subscribe("simple/topic", qos=0)
        ret = self._packet_fire(self._c)
        print(ret)

        # we expect no response for qos 0 (fire & forget)
        self.assertTrue(isinstance(ret, EventSuback))
        self.assertEqual(len(ret.reasons), 1)
        self.assertEqual(ret.reasons[0], r.REASON_GRANTED_QOS0)

    def test_02_subscribe_qos2(self):
        ret = self._c.subscribe("simple/topic", qos=1)
        ret = self._packet_fire(self._c)
        print(ret)

        # we expect no response for qos 0 (fire & forget)
        self.assertTrue(isinstance(ret, EventSuback))
        self.assertEqual(len(ret.reasons), 1)
        self.assertEqual(ret.reasons[0], r.REASON_GRANTED_QOS1)

    def test_03_subscribe_wildcards(self):
        ret = self._c.subscribe("topic/+/with/wildcards/#", qos=1)
        ret = self._packet_fire(self._c)
        print(ret)

        # we expect no response for qos 0 (fire & forget)
        self.assertTrue(isinstance(ret, EventSuback))
        self.assertEqual(len(ret.reasons), 1)
        self.assertEqual(ret.reasons[0], r.REASON_GRANTED_QOS1)

    def test_05_subscribe_multi(self):
        ret = self._c.subscribe_multi([
                ("multi/topic/0", 0, {}),
                ("multi/topic/1", 1, {}),
                ("multi/topic/#", 1, {}),
                ("multi/+/topic", 0, {}),
            ])
        ret = self._packet_fire(self._c)
        print(ret)

        self.assertTrue(isinstance(ret, EventSuback))
        self.assertEqual(ret.reasons, [0, 1, 1, 0])

    def test_06_subscribe_options(self):
        ret = self._c.subscribe_multi([
                ("subscribe/options/0", 0, {'no-local': True}),
                ("subscribe/options/1", 1, {'retain-as-published': True}),
                ("subscribe/options/2", 0, {'retain-handling': NC.RETAIN_SEND_ONLY_IF_NEW}),
                ("subscribe/options/3", 1, {'retain-handling': NC.RETAIN_DO_NOT_SEND}),
            ])
        ret = self._packet_fire(self._c)
        print(ret)

        self.assertTrue(isinstance(ret, EventSuback))
        self.assertEqual(ret.reasons, [0, 1, 0, 1])


    def test_20_unspecified_error(self):
        ret = self._c.subscribe("test/nosubscribe", qos=1)
        ret = self._packet_fire(self._c)
        print(ret)

        # we expect no response for qos 0 (fire & forget)
        self.assertTrue(isinstance(ret, EventSuback))
        self.assertEqual(len(ret.reasons), 1)
        self.assertEqual(ret.reasons[0], r.REASON_UNSPECIFIED_ERR)

    def test_21_downgraded_qos_1to0(self):
        ret = self._c.subscribe("test/QoS 0 only", qos=1)
        ret = self._packet_fire(self._c)
        print(ret)

        # we expect no response for qos 0 (Wire & forget)
        self.assertTrue(isinstance(ret, EventSuback))
        self.assertEqual(len(ret.reasons), 1)
        self.assertEqual(ret.reasons[0], r.REASON_GRANTED_QOS0)

    def test_22_invalid_topic_filter(self):
        """
            NOTE: paho testing is currently closing the connection
                  it should return 0x8F reason instead (Topic Filter invalid)
        """
        ret = self._c.subscribe("invalid/#/topic", qos=1)
        ret = self._packet_fire(self._c)
        print(ret)

        self.assertEqual(ret, None)

    def test_23_invalid_subscribe_option_retain_handling(self):
        ret = self._c.subscribe("subscribe/bad/option", 1, {'retain-handling': 0x03})
        ret = self._packet_fire(self._c)
        print(ret)

        #NOTE: according to #4.13.1, server SHOULD send a disconnect message w/ reason code
        #      but paho.mqtt.testing is not currently
        self.assertEqual(ret, None)
        self.assertFalse(self._c.conn_is_alive())


if __name__ == '__main__':
    unittest.main()
