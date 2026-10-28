from __future__ import annotations

import argparse
import math
import sys
from collections.abc import Callable, Sequence

from .probe import HopResult, TraceError, trace
from .statistics import summarize_hop


def _positive_integer(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be a positive integer") from exc
    if parsed <= 0:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return parsed


def _positive_timeout(value: str) -> float:
    try:
        parsed = float(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be a positive finite number") from exc
    if not math.isfinite(parsed) or parsed <= 0:
        raise argparse.ArgumentTypeError("must be a positive finite number")
    return parsed


def _hop_limit(value: str) -> int:
    parsed = _positive_integer(value)
    if parsed > 255:
        raise argparse.ArgumentTypeError("must be between 1 and 255")
    return parsed


def parse_arguments(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="pyroute-mtr",
        description="Trace an IPv4 route using ICMP echo probes.",
    )
    parser.add_argument("target", help="target hostname or IPv4 address")
    parser.add_argument(
        "-c",
        "--count",
        type=_positive_integer,
        default=3,
        metavar="COUNT",
        help="probes per hop (default: 3)",
    )
    parser.add_argument(
        "-w",
        "--timeout",
        type=_positive_timeout,
        default=1.0,
        metavar="SECONDS",
        help="timeout per probe in seconds (default: 1)",
    )
    parser.add_argument(
        "-m",
        "--max-hops",
        type=_hop_limit,
        default=30,
        metavar="HOPS",
        help="maximum number of hops (default: 30)",
    )
    return parser.parse_args(argv)


def _format_ms(value: float | None) -> str:
    return f"{value:.2f}" if value is not None else "-"


def format_table(hops: Sequence[HopResult]) -> str:
    headers = ("Hop", "Address", "Sent", "Recv", "Loss", "Min ms", "Avg ms", "Max ms")
    rows = []
    for hop in hops:
        stats = summarize_hop(hop)
        rows.append(
            (
                str(stats.ttl),
                stats.responder_ipv4 or "*",
                str(stats.sent_count),
                str(stats.received_count),
                (
                    f"{stats.packet_loss_percent:.1f}%"
                    if stats.packet_loss_percent is not None
                    else "-"
                ),
                _format_ms(stats.min_rtt_ms),
                _format_ms(stats.average_rtt_ms),
                _format_ms(stats.max_rtt_ms),
            )
        )

    widths = [
        max(len(headers[index]), *(len(row[index]) for row in rows))
        if rows
        else len(headers[index])
        for index in range(len(headers))
    ]
    header_line = "  ".join(
        header.ljust(widths[index]) for index, header in enumerate(headers)
    )
    divider = "  ".join("-" * width for width in widths)
    output = [header_line, divider]
    output.extend(
        "  ".join(value.ljust(widths[index]) for index, value in enumerate(row))
        for row in rows
    )
    return "\n".join(output)


def _report_probe_errors(hops: Sequence[HopResult], stream) -> None:
    for hop in hops:
        for probe in hop.probes:
            if probe.outcome == "network_error":
                detail = probe.detail or "unspecified network error"
                print(
                    f"Probe error at hop {hop.ttl} (probe {probe.sequence}): {detail}",
                    file=stream,
                )


def main(
    argv: Sequence[str] | None = None,
    *,
    trace_function: Callable[..., list[HopResult]] | None = None,
) -> int:
    args = parse_arguments(argv)
    run_trace = trace_function or trace

    try:
        hops = run_trace(
            args.target,
            count=args.count,
            timeout=args.timeout,
            max_hops=args.max_hops,
        )
    except TraceError as exc:
        print(f"pyroute-mtr: {exc}", file=sys.stderr)
        return 2

    print(format_table(hops))
    _report_probe_errors(hops, sys.stderr)
    return 0
