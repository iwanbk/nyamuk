#!/usr/bin/env python
# -*- coding: utf8 -*-

import unittest
from nyamuk import *
from nyamuk import mqtt_reasons as r

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

if __name__ == '__main__':
    unittest.main()
