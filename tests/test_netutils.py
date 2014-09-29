# Copyright 2012 OpenStack Foundation.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import socket

import mock
from oslotest import base as test_base

from oslo.utils import netutils


class NetworkUtilsTest(test_base.BaseTestCase):

    def test_no_host(self):
        result = netutils.urlsplit('http://')
        self.assertEqual('', result.netloc)
        self.assertEqual(None, result.port)
        self.assertEqual(None, result.hostname)
        self.assertEqual('http', result.scheme)

    def test_parse_host_port(self):
        self.assertEqual(('server01', 80),
                         netutils.parse_host_port('server01:80'))
        self.assertEqual(('server01', None),
                         netutils.parse_host_port('server01'))
        self.assertEqual(('server01', 1234),
                         netutils.parse_host_port('server01',
                         default_port=1234))
        self.assertEqual(('::1', 80),
                         netutils.parse_host_port('[::1]:80'))
        self.assertEqual(('::1', None),
                         netutils.parse_host_port('[::1]'))
        self.assertEqual(('::1', 1234),
                         netutils.parse_host_port('[::1]',
                         default_port=1234))
        self.assertEqual(('2001:db8:85a3::8a2e:370:7334', 1234),
                         netutils.parse_host_port(
                             '2001:db8:85a3::8a2e:370:7334',
                             default_port=1234))

    def test_urlsplit(self):
        result = netutils.urlsplit('rpc://myhost?someparam#somefragment')
        self.assertEqual(result.scheme, 'rpc')
        self.assertEqual(result.netloc, 'myhost')
        self.assertEqual(result.path, '')
        self.assertEqual(result.query, 'someparam')
        self.assertEqual(result.fragment, 'somefragment')

        result = netutils.urlsplit(
            'rpc://myhost/mypath?someparam#somefragment',
            allow_fragments=False)
        self.assertEqual(result.scheme, 'rpc')
        self.assertEqual(result.netloc, 'myhost')
        self.assertEqual(result.path, '/mypath')
        self.assertEqual(result.query, 'someparam#somefragment')
        self.assertEqual(result.fragment, '')

        result = netutils.urlsplit(
            'rpc://user:pass@myhost/mypath?someparam#somefragment',
            allow_fragments=False)
        self.assertEqual(result.scheme, 'rpc')
        self.assertEqual(result.netloc, 'user:pass@myhost')
        self.assertEqual(result.path, '/mypath')
        self.assertEqual(result.query, 'someparam#somefragment')
        self.assertEqual(result.fragment, '')

    def test_urlsplit_ipv6(self):
        ipv6_url = 'http://[::1]:443/v2.0/'
        result = netutils.urlsplit(ipv6_url)
        self.assertEqual(result.scheme, 'http')
        self.assertEqual(result.netloc, '[::1]:443')
        self.assertEqual(result.path, '/v2.0/')
        self.assertEqual(result.hostname, '::1')
        self.assertEqual(result.port, 443)

        ipv6_url = 'http://user:pass@[::1]/v2.0/'
        result = netutils.urlsplit(ipv6_url)
        self.assertEqual(result.scheme, 'http')
        self.assertEqual(result.netloc, 'user:pass@[::1]')
        self.assertEqual(result.path, '/v2.0/')
        self.assertEqual(result.hostname, '::1')
        self.assertEqual(result.port, None)

        ipv6_url = 'https://[2001:db8:85a3::8a2e:370:7334]:1234/v2.0/xy?ab#12'
        result = netutils.urlsplit(ipv6_url)
        self.assertEqual(result.scheme, 'https')
        self.assertEqual(result.netloc, '[2001:db8:85a3::8a2e:370:7334]:1234')
        self.assertEqual(result.path, '/v2.0/xy')
        self.assertEqual(result.hostname, '2001:db8:85a3::8a2e:370:7334')
        self.assertEqual(result.port, 1234)
        self.assertEqual(result.query, 'ab')
        self.assertEqual(result.fragment, '12')

    def test_urlsplit_params(self):
        test_url = "http://localhost/?a=b&c=d"
        result = netutils.urlsplit(test_url)
        self.assertEqual({'a': 'b', 'c': 'd'}, result.params())
        self.assertEqual({'a': 'b', 'c': 'd'}, result.params(collapse=False))

        test_url = "http://localhost/?a=b&a=c&a=d"
        result = netutils.urlsplit(test_url)
        self.assertEqual({'a': 'd'}, result.params())
        self.assertEqual({'a': ['b', 'c', 'd']}, result.params(collapse=False))

        test_url = "http://localhost"
        result = netutils.urlsplit(test_url)
        self.assertEqual({}, result.params())

        test_url = "http://localhost?"
        result = netutils.urlsplit(test_url)
        self.assertEqual({}, result.params())

    def test_set_tcp_keepalive(self):
        mock_sock = mock.Mock()
        netutils.set_tcp_keepalive(mock_sock, True, 100, 10, 5)
        calls = [
            mock.call.setsockopt(socket.SOL_SOCKET,
                                 socket.SO_KEEPALIVE, True),
        ]
        if hasattr(socket, 'TCP_KEEPIDLE'):
            calls += [
                mock.call.setsockopt(socket.IPPROTO_TCP,
                                     socket.TCP_KEEPIDLE, 100)
            ]
        if hasattr(socket, 'TCP_KEEPINTVL'):
            calls += [
                mock.call.setsockopt(socket.IPPROTO_TCP,
                                     socket.TCP_KEEPINTVL, 10),
            ]
        if hasattr(socket, 'TCP_KEEPCNT'):
            calls += [
                mock.call.setsockopt(socket.IPPROTO_TCP,
                                     socket.TCP_KEEPCNT, 5)
            ]
        mock_sock.assert_has_calls(calls)

        mock_sock.reset_mock()
        netutils.set_tcp_keepalive(mock_sock, False)
        self.assertEqual(1, len(mock_sock.mock_calls))

    def test_is_valid_ipv4(self):
        self.assertTrue(netutils.is_valid_ipv4('42.42.42.42'))

        self.assertFalse(netutils.is_valid_ipv4('-1.11.11.11'))

        self.assertFalse(netutils.is_valid_ipv4(''))

    def test_is_valid_ipv6(self):
        self.assertTrue(netutils.is_valid_ipv6('::1'))

        self.assertFalse(netutils.is_valid_ipv6(
            '1fff::a88:85a3::172.31.128.1'))

        self.assertFalse(netutils.is_valid_ipv6(''))

    def test_is_valid_ip(self):
        self.assertTrue(netutils.is_valid_ip('127.0.0.1'))

        self.assertTrue(netutils.is_valid_ip('2001:db8::ff00:42:8329'))

        self.assertFalse(netutils.is_valid_ip('256.0.0.0'))

        self.assertFalse(netutils.is_valid_ip('::1.2.3.'))

        self.assertFalse(netutils.is_valid_ip(''))