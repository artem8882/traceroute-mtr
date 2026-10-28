from __future__ import annotations

import ipaddress
import math
import os
import socket
import struct
import time
from dataclasses import dataclass
from typing import Callable, Literal


ProbeOutcome = Literal["reply", "timeout", "network_error"]


class TraceError(Exception):
    """Raised when a trace cannot be started or continued meaningfully."""


@dataclass(frozen=True)
class ProbeResult:
    ttl: int
    sequence: int
    outcome: ProbeOutcome
    responder_ipv4: str | None = None
    rtt_ms: float | None = None
    sent: bool = False
    detail: str | None = None
    reached_destination: bool = False
    icmp_type: int | None = None
    icmp_code: int | None = None


@dataclass(frozen=True)
class HopResult:
    ttl: int
    probes: list[ProbeResult]

    @property
    def responder_ipv4(self) -> str | None:
        return next(
            (
                probe.responder_ipv4
                for probe in self.probes
                if probe.outcome == "reply" and probe.responder_ipv4 is not None
            ),
            None,
        )

    @property
    def reached_destination(self) -> bool:
        return any(probe.reached_destination for probe in self.probes)


@dataclass(frozen=True)
class IcmpReply:
    message_type: int
    code: int


def _checksum(data: bytes) -> int:
    if len(data) % 2:
        data += b"\x00"

    total = sum(struct.unpack(f"!{len(data) // 2}H", data))
    total = (total & 0xFFFF) + (total >> 16)
    total = (total & 0xFFFF) + (total >> 16)
    return (~total) & 0xFFFF


def build_echo_request(identifier: int, sequence: int) -> bytes:
    payload = b"pyroute-mtr"
    header = struct.pack("!BBHHH", 8, 0, 0, identifier, sequence)
    checksum = _checksum(header + payload)
    return struct.pack("!BBHHH", 8, 0, checksum, identifier, sequence) + payload


def _ipv4_header_length(packet: bytes, offset: int) -> int | None:
    if len(packet) <= offset or packet[offset] >> 4 != 4:
        return None
    header_length = (packet[offset] & 0x0F) * 4
    if header_length < 20 or len(packet) < offset + header_length:
        return None
    return header_length


def parse_icmp_packet(
    packet: bytes, identifier: int, sequence: int
) -> IcmpReply | None:
    """Return a correlated ICMP response, ignoring unrelated or malformed packets."""
    offset = 0
    outer_header_length = _ipv4_header_length(packet, 0)
    if outer_header_length is not None:
        if packet[9] != socket.IPPROTO_ICMP:
            return None
        offset = outer_header_length
    elif packet and packet[0] >> 4 == 4:
        return None

    if len(packet) < offset + 8:
        return None

    message_type, code, _, reply_identifier, reply_sequence = struct.unpack_from(
        "!BBHHH", packet, offset
    )
    if message_type == 0:
        if (
            code == 0
            and reply_identifier == identifier
            and reply_sequence == sequence
        ):
            return IcmpReply(message_type, code)
        return None

    if message_type not in (3, 11):
        return None
    if message_type == 11 and code != 0:
        return None

    quoted_offset = offset + 8
    inner_header_length = _ipv4_header_length(packet, quoted_offset)
    if inner_header_length is None:
        return None

    inner_ip_offset = quoted_offset
    if packet[inner_ip_offset + 9] != socket.IPPROTO_ICMP:
        return None

    inner_icmp_offset = inner_ip_offset + inner_header_length
    if len(packet) < inner_icmp_offset + 8:
        return None

    request_type, _, _, request_identifier, request_sequence = struct.unpack_from(
        "!BBHHH", packet, inner_icmp_offset
    )
    if (
        request_type == 8
        and request_identifier == identifier
        and request_sequence == sequence
    ):
        return IcmpReply(message_type, code)
    return None


def resolve_ipv4(target: str) -> str:
    try:
        address = ipaddress.ip_address(target)
    except ValueError:
        address = None
    else:
        if isinstance(address, ipaddress.IPv4Address):
            return str(address)
        raise TraceError("IPv6 targets are not supported; provide a hostname or IPv4 address.")

    try:
        results = socket.getaddrinfo(
            target,
            None,
            family=socket.AF_INET,
            type=socket.SOCK_RAW,
            proto=socket.IPPROTO_ICMP,
        )
    except socket.gaierror as exc:
        raise TraceError(f"Unable to resolve target {target!r}: {exc}") from exc

    for result in results:
        try:
            return str(ipaddress.IPv4Address(result[4][0]))
        except (IndexError, ValueError):
            continue
    raise TraceError(f"Unable to resolve target {target!r} to an IPv4 address.")


def _validate_options(count: int, timeout: float, max_hops: int) -> None:
    if isinstance(count, bool) or not isinstance(count, int) or count <= 0:
        raise ValueError("probe count must be a positive integer")
    if (
        isinstance(timeout, bool)
        or not isinstance(timeout, (int, float))
        or not math.isfinite(timeout)
        or timeout <= 0
    ):
        raise ValueError("timeout must be a positive finite number")
    if (
        isinstance(max_hops, bool)
        or not isinstance(max_hops, int)
        or not 1 <= max_hops <= 255
    ):
        raise ValueError("maximum hops must be an integer between 1 and 255")


def _socket_error_message(error: OSError) -> str:
    message = f"Could not create an ICMP raw socket: {error}."
    if os.name == "nt":
        return f"{message} Windows requires an Administrator terminal for raw sockets."
    return f"{message} Try running with elevated privileges."


def _probe(
    raw_socket: socket.socket,
    destination: str,
    ttl: int,
    identifier: int,
    sequence: int,
    timeout: float,
    clock: Callable[[], float],
) -> ProbeResult:
    sent = False
    try:
        raw_socket.setsockopt(socket.IPPROTO_IP, socket.IP_TTL, ttl)
        raw_socket.settimeout(timeout)
        started = clock()
        raw_socket.sendto(
            build_echo_request(identifier, sequence), (destination, 0)
        )
        sent = True
    except OSError as exc:
        return ProbeResult(
            ttl=ttl,
            sequence=sequence,
            outcome="network_error",
            sent=sent,
            detail=str(exc),
        )

    deadline = started + timeout
    while True:
        remaining = deadline - clock()
        if remaining <= 0:
            return ProbeResult(ttl, sequence, "timeout", sent=True)

        try:
            raw_socket.settimeout(remaining)
            packet, address = raw_socket.recvfrom(65535)
        except socket.timeout:
            return ProbeResult(ttl, sequence, "timeout", sent=True)
        except OSError as exc:
            return ProbeResult(
                ttl=ttl,
                sequence=sequence,
                outcome="network_error",
                sent=True,
                detail=str(exc),
            )

        reply = parse_icmp_packet(packet, identifier, sequence)
        if reply is None:
            continue

        responder = address[0]
        reached_destination = reply.message_type == 0 and responder == destination
        return ProbeResult(
            ttl=ttl,
            sequence=sequence,
            outcome="reply",
            responder_ipv4=responder,
            rtt_ms=max(0.0, (clock() - started) * 1000),
            sent=True,
            reached_destination=reached_destination,
            icmp_type=reply.message_type,
            icmp_code=reply.code,
        )


def trace(
    target: str,
    *,
    count: int = 3,
    timeout: float = 1.0,
    max_hops: int = 30,
    socket_factory: Callable[..., socket.socket] | None = None,
    clock: Callable[[], float] = time.monotonic,
) -> list[HopResult]:
    _validate_options(count, timeout, max_hops)
    destination = resolve_ipv4(target)
    create_socket = socket_factory or socket.socket

    try:
        raw_socket = create_socket(
            socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP
        )
    except OSError as exc:
        raise TraceError(_socket_error_message(exc)) from exc

    results: list[HopResult] = []
    identifier = os.getpid() & 0xFFFF
    sequence = 0
    try:
        with raw_socket:
            for ttl in range(1, max_hops + 1):
                probes = []
                for _ in range(count):
                    sequence = (sequence % 0xFFFF) + 1
                    probes.append(
                        _probe(
                            raw_socket,
                            destination,
                            ttl,
                            identifier,
                            sequence,
                            float(timeout),
                            clock,
                        )
                    )

                hop = HopResult(ttl, probes)
                results.append(hop)
                if hop.reached_destination:
                    break
    except OSError as exc:
        raise TraceError(f"Network error while tracing {destination}: {exc}") from exc

    return results
