import unittest

from pyroute_mtr.probe import HopResult, ProbeResult
from pyroute_mtr.statistics import summarize_hop


class StatisticsTests(unittest.TestCase):
    def test_summarize_all_replies(self):
        hop = HopResult(
            ttl=2,
            probes=[
                ProbeResult(2, 1, "reply", "192.0.2.1", 4.0, sent=True),
                ProbeResult(2, 2, "reply", "192.0.2.1", 8.0, sent=True),
                ProbeResult(2, 3, "reply", "192.0.2.1", 6.0, sent=True),
            ],
        )

        stats = summarize_hop(hop)

        self.assertEqual(stats.sent_count, 3)
        self.assertEqual(stats.received_count, 3)
        self.assertEqual(stats.packet_loss_percent, 0.0)
        self.assertEqual(stats.min_rtt_ms, 4.0)
        self.assertEqual(stats.average_rtt_ms, 6.0)
        self.assertEqual(stats.max_rtt_ms, 8.0)

    def test_summarize_mixed_replies_and_timeouts(self):
        hop = HopResult(
            ttl=1,
            probes=[
                ProbeResult(1, 1, "reply", "192.0.2.1", 10.0, sent=True),
                ProbeResult(1, 2, "timeout", sent=True),
                ProbeResult(1, 3, "reply", "192.0.2.1", 30.0, sent=True),
            ],
        )

        stats = summarize_hop(hop)

        self.assertEqual(stats.sent_count, 3)
        self.assertEqual(stats.received_count, 2)
        self.assertAlmostEqual(stats.packet_loss_percent, 100 / 3)
        self.assertEqual(stats.min_rtt_ms, 10.0)
        self.assertEqual(stats.average_rtt_ms, 20.0)
        self.assertEqual(stats.max_rtt_ms, 30.0)

    def test_summarize_unanswered_hop_has_no_rtt_or_address(self):
        hop = HopResult(
            ttl=4,
            probes=[
                ProbeResult(4, 1, "timeout", sent=True),
                ProbeResult(4, 2, "timeout", sent=True),
            ],
        )

        stats = summarize_hop(hop)

        self.assertEqual(stats.packet_loss_percent, 100.0)
        self.assertIsNone(stats.responder_ipv4)
        self.assertIsNone(stats.min_rtt_ms)
        self.assertIsNone(stats.average_rtt_ms)
        self.assertIsNone(stats.max_rtt_ms)

    def test_unsent_network_error_is_not_counted_as_packet_loss(self):
        hop = HopResult(
            ttl=1,
            probes=[ProbeResult(1, 1, "network_error", detail="send failed")],
        )

        stats = summarize_hop(hop)

        self.assertEqual(stats.sent_count, 0)
        self.assertEqual(stats.received_count, 0)
        self.assertIsNone(stats.packet_loss_percent)


if __name__ == "__main__":
    unittest.main()
