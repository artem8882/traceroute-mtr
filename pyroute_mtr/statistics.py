from dataclasses import dataclass
from statistics import mean

from .probe import HopResult


@dataclass(frozen=True)
class HopStatistics:
    ttl: int
    responder_ipv4: str | None
    sent_count: int
    received_count: int
    packet_loss_percent: float | None
    min_rtt_ms: float | None
    average_rtt_ms: float | None
    max_rtt_ms: float | None


def summarize_hop(hop: HopResult) -> HopStatistics:
    sent_count = sum(probe.sent for probe in hop.probes)
    received = [
        probe for probe in hop.probes if probe.outcome == "reply" and probe.rtt_ms is not None
    ]
    rtts = [probe.rtt_ms for probe in received if probe.rtt_ms is not None]
    received_count = len(received)
    packet_loss = (
        (sent_count - received_count) / sent_count * 100 if sent_count else None
    )

    return HopStatistics(
        ttl=hop.ttl,
        responder_ipv4=hop.responder_ipv4,
        sent_count=sent_count,
        received_count=received_count,
        packet_loss_percent=packet_loss,
        min_rtt_ms=min(rtts) if rtts else None,
        average_rtt_ms=mean(rtts) if rtts else None,
        max_rtt_ms=max(rtts) if rtts else None,
    )
