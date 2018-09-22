#!/usr/bin/env python
# -*- coding: utf8 -*-

import unittest
from nyamuk import *
from nyamuk import mqtt_reasons as r
from nyamuk import nyamuk_prop as p

class PublishTest(unittest.TestCase):
    def _packet_fire(self, c):
        c.packet_write()
        r = c.loop()

        return c.pop_event()

    def _fake_subscriber(self, topic):
        self._fake = Nyamuk("fake_subscr", server="localhost")
        ret = self._fake.connect(version=5)
        ret = self._packet_fire(self._fake)

        self._fake.subscribe(topic, qos=1)
        self._packet_fire(self._fake)

    def _fake_publisher(self):
        self._fake = Nyamuk("fake_pub", server="localhost")
        ret = self._fake.connect(version=5)
        ret = self._packet_fire(self._fake)

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

    def test_03_valid_qos2(self):
        # init
        self._fake_subscriber("foo/bar")
        # /

        ret = self._c.publish("foo/bar", "foo/bar,qos=2", qos=2)
        ret = self._packet_fire(self._c)
        print(ret)

        self.assertTrue(isinstance(ret, EventPubrec))
        self.assertEqual(ret.reason, r.REASON_SUCCESS)

        ret = self._c.pubrel(ret.mid)
        ret = self._packet_fire(self._c)
        print(ret)

        self.assertTrue(isinstance(ret, EventPubcomp))
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

    def test_30_pubrec_invalid_pktid(self):
        # init
        self._fake_subscriber("foo/bar")
        # /

        ret = self._c.publish("foo/bar", "foo/bar,qos=2/err", qos=2)
        ret = self._packet_fire(self._c)
        print(ret)

        self.assertTrue(isinstance(ret, EventPubrec))
        self.assertEqual(ret.reason, r.REASON_SUCCESS)

        #ret = self._c.pubrel(42, props=[p.UserProperty((u'foo',u'bar'))])
        ret = self._c.pubrel(42, props=[p.ReasonString(u'poo')])
        #ret = self._c.pubrel(42)
        ret = self._packet_fire(self._c)
        print(ret)

        self.assertTrue(isinstance(ret, EventPubcomp))
        self.assertEqual(ret.reason, r.REASON_PACKET_ID_NOT_FOUND)


    def test_50_publish_receiver_qos0(self):
        # init
        self._fake_publisher()
        # /

        ret = self._c.subscribe("foo/+", qos=0)
        ret = self._packet_fire(self._c)
        print(ret)


        self._fake.publish('foo/bar', 'test/qos0', qos=1)
        self._packet_fire(self._fake)

        ret = self._packet_fire(self._c)
        print(ret)
        self.assertTrue(isinstance(ret, EventPublish))
        self.assertEqual(ret.msg.topic  , "foo/bar")
        self.assertEqual(ret.msg.payload, "test/qos0")
        self.assertEqual(ret.msg.qos    , 0)

    def test_51_publish_receiver_qos1(self):
        # init
        self._fake_publisher()
        # /

        ret = self._c.subscribe("foo/+", qos=1)
        ret = self._packet_fire(self._c)
        print(ret)


        self._fake.publish('foo/bar', 'test/qos1', qos=1, props=[
                p.ResponseTopic("answer/here")
            ])
        self._packet_fire(self._fake)

        ret = self._packet_fire(self._c)
        print(ret)
        self.assertTrue(isinstance(ret, EventPublish))
        self.assertEqual(ret.msg.topic  , "foo/bar")
        self.assertEqual(ret.msg.payload, "test/qos1")
        self.assertEqual(ret.msg.qos    , 1)


        ret = self._c.puback(ret.msg.mid, reason=r.REASON_SUCCESS)
        ret = self._packet_fire(self._c)
        print(ret)

    def test_52_publish_receiver_qos2(self):
        # init
        self._fake_publisher()
        # /

        ret = self._c.subscribe("foo/+", qos=2)
        ret = self._packet_fire(self._c)
        print(ret)


        # NOTE: publisher qos have to be 2 for subscriber to receive a qos 2 message
        #       (not by the book but this is how paho.mqtt.testing is implemented)
        self._fake.publish('foo/bar', 'test/qos2', qos=2)
        self._packet_fire(self._fake)

        ret = self._packet_fire(self._c)
        print(ret)
        self.assertTrue(isinstance(ret, EventPublish))
        self.assertEqual(ret.msg.topic  , "foo/bar")
        self.assertEqual(ret.msg.payload, "test/qos2")
        self.assertEqual(ret.msg.qos    , 2)

        ret = self._c.pubrec(ret.msg.mid, reason=r.REASON_SUCCESS)
        ret = self._packet_fire(self._c)
        print(ret)

        self.assertTrue(isinstance(ret, EventPubrel))
        self.assertEqual(ret.reason, r.REASON_SUCCESS)

        ret = self._c.pubcomp(ret.mid, reason=r.REASON_SUCCESS)
        ret = self._packet_fire(self._c)
        print(ret)


if __name__ == '__main__':
    unittest.main()
