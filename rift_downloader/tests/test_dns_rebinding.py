import socket
import unittest
from unittest.mock import patch

from rift_downloader.http import UnsafeURL,guarded_dns

class DNSRebindingTests(unittest.TestCase):
    def test_private_ip_on_actual_connect_rejected(self):
        private=[(socket.AF_INET,socket.SOCK_STREAM,6,'',('169.254.169.254',443))]
        with patch('rift_downloader.http.socket.getaddrinfo',return_value=private):
            with self.assertRaises(UnsafeURL):
                with guarded_dns():
                    socket.getaddrinfo('public.example.org',443)
    def test_ipv4_mapped_ipv6_local_address_rejected(self):
        private=[(socket.AF_INET6,socket.SOCK_STREAM,6,'',('::ffff:127.0.0.1',443,0,0))]
        with patch('rift_downloader.http.socket.getaddrinfo',return_value=private):
            with self.assertRaises(UnsafeURL):
                with guarded_dns():
                    socket.getaddrinfo('public.example.org',443)
    def test_public_ip_still_works_and_global_resolver_is_restored(self):
        public=[(socket.AF_INET,socket.SOCK_STREAM,6,'',('8.8.8.8',443))]
        with patch('rift_downloader.http.socket.getaddrinfo',return_value=public) as mock:
            before=socket.getaddrinfo
            with guarded_dns():
                self.assertEqual(socket.getaddrinfo('public.example.org',443),public)
                self.assertIsNot(socket.getaddrinfo,before)
            self.assertIs(socket.getaddrinfo,before)
            self.assertEqual(mock.call_count,1)

if __name__=='__main__':unittest.main()
