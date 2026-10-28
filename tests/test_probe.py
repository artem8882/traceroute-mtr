import socket
import struct
import unittest
from unittest import mock

from pyroute_mtr.probe import (
    TraceError,
    build_echo_request,
    parse_icmp_packet,
    trace,
)


def ipv4_packet(source, destination, payload, protocol=socket.IPPROTO_ICMP):
    source_bytes = socket.inet_aton(source)
    destination_bytes = socket.inet_aton(destination)
    header = struct.pack(
        "!BBHHHBBH4s4s",
        0x45,
        0,
        20 + len(payload),
        0,
        0,
        64,
        protocol,
        0,
        source_bytes,
        destination_bytes,
    )
    return header + payload


def icmp_message(message_type, code, payload=b""):
    return struct.pack("!BBHHH", message_type, code, 0, 0, 0) + payload


class FakeSocket:
    def __init__(
        self,
        responses_by_ttl,
        *,
        send_error_at_ttl=None,
        recv_error_at_ttl=None,
    ):
        self.responses_by_ttl = responses_by_ttl
        self.send_error_at_ttl = send_error_at_ttl
        self.recv_error_at_ttl = recv_error_at_ttl
        self.ttl = None
        self.responses = []
        self.sent = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def setsockopt(self, level, option, value):
        self.ttl = value

    def settimeout(self, timeout):
        self.timeout = timeout

    def sendto(self, packet, destination):
        self.sent.append((self.ttl, packet, destination))
        if self.ttl == self.send_error_at_ttl:
            raise OSError("network unreachable")
        response = self.responses_by_ttl.get(self.ttl)
        if response == "timeout":
            return

        identifier, sequence = struct.unpack("!HH", packet[4:8])
        if response == "ttl":
            original_ip = ipv4_packet("192.0.2.10", destination[0], packet)
            self.responses.append(
                (
                    ipv4_packet(
                        "192.0.2.1",
                        "192.0.2.10",
                        icmp_message(11, 0, original_ip),
                    ),
                    ("192.0.2.1", 0),
                )
            )
        elif response == "destination":
            self.responses.append(
                (
                    ipv4_packet(
                        destination[0],
                        "192.0.2.10",
                        struct.pack("!BBHHH", 0, 0, 0, identifier, sequence),
                    ),
                    (destination[0], 0),
                )
            )
        elif response == "unmatched-then-ttl":
            self.responses.append(
                (
                    ipv4_packet(
                        "192.0.2.9",
                        "192.0.2.10",
                        struct.pack("!BBHHH", 0, 0, 0, identifier + 1, sequence),
                    ),
                    ("192.0.2.9", 0),
                )
            )
            original_ip = ipv4_packet("192.0.2.10", destination[0], packet)
            self.responses.append(
                (
                    ipv4_packet(
                        "192.0.2.1",
                        "192.0.2.10",
                        icmp_message(11, 0, original_ip),
                    ),
                    ("192.0.2.1", 0),
                )
            )

    def recvfrom(self, buffer_size):
        if self.ttl == self.recv_error_at_ttl:
            raise OSError("receive failed")
        if not self.responses:
            raise socket.timeout
        return self.responses.pop(0)


class ProbeTests(unittest.TestCase):
    def test_build_echo_request_contains_identifier_and_sequence(self):
        packet = build_echo_request(0x1234, 0x5678)

        self.assertEqual(packet[0:2], b"\x08\x00")
        self.assertEqual(struct.unpack("!HH", packet[4:8]), (0x1234, 0x5678))
        self.assertGreater(len(packet), 8)

    def test_parse_ttl_exceeded_correlates_quoted_echo_request(self):
        request = build_echo_request(123, 7)
        inner_ip = ipv4_packet("192.0.2.10", "203.0.113.2", request)
        response = ipv4_packet(
            "192.0.2.1", "192.0.2.10", icmp_message(11, 0, inner_ip)
        )

        reply = parse_icmp_packet(response, 123, 7)

        self.assertIsNotNone(reply)
        self.assertEqual(reply.message_type, 11)
        self.assertEqual(reply.code, 0)

    def test_parse_ignores_reply_for_another_probe(self):
        response = ipv4_packet(
            "203.0.113.2",
            "192.0.2.10",
            struct.pack("!BBHHH", 0, 0, 0, 123, 8),
        )

        self.assertIsNone(parse_icmp_packet(response, 123, 7))

    def test_trace_advances_after_timeout_and_stops_at_destination(self):
        fake_socket = FakeSocket(
            {1: "timeout", 2: "ttl", 3: "destination", 4: "ttl"}
        )

        hops = trace(
            "203.0.113.2",
            count=1,
            max_hops=5,
            socket_factory=lambda *args: fake_socket,
        )

        self.assertEqual([hop.ttl for hop in hops], [1, 2, 3])
        self.assertIsNone(hops[0].probes[0].responder_ipv4)
        self.assertEqual(hops[1].probes[0].responder_ipv4, "192.0.2.1")
        self.assertTrue(hops[2].probes[0].reached_destination)
        self.assertEqual([ttl for ttl, _, _ in fake_socket.sent], [1, 2, 3])

    def test_trace_ignores_unmatched_packet_then_accepts_correlated_reply(self):
        fake_socket = FakeSocket({1: "unmatched-then-ttl"})

        hops = trace(
            "203.0.113.2",
            count=1,
            max_hops=1,
            socket_factory=lambda *args: fake_socket,
        )

        self.assertEqual(hops[0].probes[0].responder_ipv4, "192.0.2.1")
        self.assertEqual(hops[0].probes[0].outcome, "reply")

    def test_hostname_resolution_selects_ipv4_once(self):
        fake_socket = FakeSocket({1: "destination"})

        with mock.patch(
            "pyroute_mtr.probe.socket.getaddrinfo",
            return_value=[
                (socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP, "", ("203.0.113.2", 0))
            ],
        ) as resolver:
            hops = trace(
                "example.test",
                count=1,
                max_hops=1,
                socket_factory=lambda *args: fake_socket,
            )

        resolver.assert_called_once()
        self.assertTrue(hops[0].reached_destination)

    def test_send_network_error_is_reported_and_later_ttl_is_probed(self):
        fake_socket = FakeSocket(
            {2: "destination"},
            send_error_at_ttl=1,
        )

        hops = trace(
            "203.0.113.2",
            count=1,
            max_hops=2,
            socket_factory=lambda *args: fake_socket,
        )

        self.assertEqual(hops[0].probes[0].outcome, "network_error")
        self.assertFalse(hops[0].probes[0].sent)
        self.assertIn("network unreachable", hops[0].probes[0].detail)
        self.assertTrue(hops[1].reached_destination)

    def test_receive_network_error_is_reported_as_sent_but_unanswered(self):
        fake_socket = FakeSocket({}, recv_error_at_ttl=1)

        hops = trace(
            "203.0.113.2",
            count=1,
            max_hops=1,
            socket_factory=lambda *args: fake_socket,
        )

        self.assertEqual(hops[0].probes[0].outcome, "network_error")
        self.assertTrue(hops[0].probes[0].sent)
        self.assertIn("receive failed", hops[0].probes[0].detail)

    def test_raw_socket_permission_error_has_windows_guidance(self):
        def denied_socket(*args):
            raise PermissionError("access denied")

        with mock.patch("pyroute_mtr.probe.os.name", "nt"):
            with self.assertRaisesRegex(TraceError, "Administrator"):
                trace("203.0.113.2", socket_factory=denied_socket)

    def test_ipv6_target_is_rejected(self):
        with self.assertRaisesRegex(TraceError, "IPv6 targets are not supported"):
            trace("2001:db8::1")


if __name__ == "__main__":
    unittest.main()
