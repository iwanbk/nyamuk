#!/usr/bin/env python
# -*- coding: utf8 -*-

import time
import unittest
from nyamuk import *
from nyamuk import mqtt_reasons as r
from nyamuk import nyamuk_prop as p

class ConnectTest(unittest.TestCase):
    def _packet_fire(self, c):
        c.packet_write()
        r = c.loop()

        return c.pop_event()

    def _test_sample(self):
        self.assertTrue(True)

    # valid connect
    def test_01_success(self):
        c = Nyamuk("unittest", server="localhost")
        ret = c.connect(version=5)
        ret = self._packet_fire(c)

        self.assertTrue(isinstance(ret, EventConnack))
        self.assertEqual(ret.ret_code, r.REASON_SUCCESS)
        self.assertTrue(c.conn_is_alive())

    def test_02_invalid_protocol_name(self):
        NC.specs[5]['name'] = 'ZQTT'

        c = Nyamuk("unittest", server="localhost")
        ret = c.connect(version=5)
        ret = self._packet_fire(c)

        NC.specs[5]['name'] = 'MQTT'

        self.assertEqual(ret, None)
        self.assertFalse(c.conn_is_alive())

    def test_03_invalid_protocol_version(self):
        """
            NOTE: paho testsuite is closing connection without sending 0x84 error code
        """
        NC.specs[6] = {'name':'MQTT','hdrsize': 10}

        c = Nyamuk("unittest", server="localhost")
        ret = c.connect(version=6)
        ret = self._packet_fire(c)

        self.assertEqual(ret, None)
        self.assertFalse(c.conn_is_alive())

    def test_04_serverside_clientid(self):
        """
            Server may allow client to supply a 0-length client-id
            If so, it must assign a unique client-id
        """
        c = Nyamuk(None, server='localhost')
        self.assertEqual(c.client_id, None)

        ret = c.connect(version=5)
        ret = self._packet_fire(c)
        print(ret)

        self.assertTrue(isinstance(ret, EventConnack))
        # assigned client-id is returned as property
        cid = filter(lambda x: isinstance(x, p.AssignedClientId), ret.props)
        self.assertTrue(len(cid), 1)

        # returned client-id is automatically assigned to the client object
        self.assertNotEqual(c.client_id, None)
        print(c.client_id)

    def test_05_utf8_clientid(self):
        # clientid length is 20 bytes
        c = Nyamuk(u"ütf8 clîentid 😄", server="localhost")
        ret = c.connect(version=5)
        ret = self._packet_fire(c)

        self.assertTrue(isinstance(ret, EventConnack))
        self.assertEqual(ret.ret_code, r.REASON_SUCCESS)
        self.assertTrue(c.conn_is_alive())

    def test_06_will_simple(self):
        c = Nyamuk('test-will', server='localhost')
        ret = c.connect(version=5, will={
            'topic'  : 'last/will',
            'message': 'I\'m dying...',
            'qos'    : 1
        })
        ret = self._packet_fire(c)
        print(ret)

        subscr = Nyamuk("fake_subscrr", server="localhost")
        ret = subscr.connect(version=5)
        ret = self._packet_fire(subscr)

        subscr.subscribe('last/will', qos=0)
        self._packet_fire(subscr)

        self.assertTrue(isinstance(ret, EventConnack))
        self.assertEqual(ret.ret_code, r.REASON_SUCCESS)
        self.assertTrue(c.conn_is_alive())

        c.socket_close()

        ret = self._packet_fire(subscr)
        print(ret)
        self.assertTrue(isinstance(ret, EventPublish))
        self.assertEqual(ret.msg.topic, 'last/will')
        self.assertEqual(ret.msg.payload, 'I\'m dying...')

        subscr.socket_close()

    def test_07_will_properties(self):
        c = Nyamuk('test-will', server='localhost')
        ret = c.connect(version=5, will={
            'topic'  : 'last/will',
            'message': 'I\'m dying again...',
            'qos'    : 1,

            'props'  : [
                p.UserProperty(('hello','i\'m dead')),
                p.WillDelayInterval(0),
                p.PayloadFormatIndicator(1),
                p.MessageExpiryInterval(10),
                p.ContentType('text/plain; charset=UTF-8'),
                p.ResponseTopic('will/response/topic'),
                #p.CorrelationData(bytearray('foobar')),
                p.CorrelationData('föobar'),
            ]
        })
        ret = self._packet_fire(c)
        print(ret)

        subscr = Nyamuk("fake_subscr", server="localhost")
        ret = subscr.connect(version=5)
        ret = self._packet_fire(subscr)

        subscr.subscribe('last/will', qos=0)
        self._packet_fire(subscr)

        self.assertTrue(isinstance(ret, EventConnack))
        self.assertEqual(ret.ret_code, r.REASON_SUCCESS)
        self.assertTrue(c.conn_is_alive())

        c.socket_close()
        time.sleep(1)

        ret = self._packet_fire(subscr)
        print(ret)
        self.assertTrue(isinstance(ret, EventPublish))
        self.assertEqual(ret.msg.topic, 'last/will')
        self.assertEqual(ret.msg.payload, 'I\'m dying again...')
        # Will delay interval is not propagated
        self.assertEqual(len(ret.props), 6)

        subscr.socket_close()

if __name__ == '__main__':
    unittest.main()
