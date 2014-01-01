#!/usr/bin/env python
import os
import subprocess
import sys
import unittest

from xonrequest import Xor

simple_rule = {'route': '/t1/<val1>',
        'output': True,
        'script': 'files/slow.sh'}

class RunscriptSlowTest(unittest.TestCase):
    def setUp(self):
        self.x = Xor()
        self.x.app.testing = True

    def test_slow_printing(self):
        self.x.add_rules([simple_rule])
        client = self.x.app.test_client()
        test_string = '1 2 3 4 5 6'
        rv = client.get('/t1/%s' % test_string)
        self.assertEqual(test_string, rv.data.strip())
