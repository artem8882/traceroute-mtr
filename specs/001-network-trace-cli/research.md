# Research: Network Trace CLI

## ICMP probing and Windows support

**Decision**: Use IPv4 raw ICMP echo sockets from Python's standard `socket` module. Set `IP_TTL` to the current hop number before sending each echo request. Parse returned ICMP packets to distinguish echo replies, TTL-expired responses, and destination-unreachable responses; correlate replies with the current probe identifier and sequence number.

**Rationale**: Raw ICMP requests and per-socket TTL directly satisfy the requirement to send ICMP packets at successively increasing TTL values. The standard library provides the required socket operations without runtime dependencies. Windows supports `SOCK_RAW`, but Microsoft's Winsock documentation states that only administrators can create raw sockets on current Windows versions; report permission failures clearly and document running an elevated terminal.

**Alternatives considered**:
- Calling Windows `tracert.exe`: rejected because it is platform-specific and its presentation and probe behavior are harder to control and unit-test.
- UDP traceroute probes: rejected because the user explicitly requires ICMP packets.
- Third-party ICMP libraries: rejected because a dependency is unnecessary and the user prefers the standard library.

## Destination resolution

**Decision**: Accept IPv4 literals and hostnames. Resolve hostnames once before tracing, select one IPv4 result, and use that address consistently for all hops.

**Rationale**: This meets the IPv4-only input requirement and the spec's consistency assumption. Resolving once avoids address changes during a trace and makes invalid names fail before any probes are sent.

**Alternatives considered**:
- Re-resolving before each hop: rejected because a hostname could map to different addresses during one trace.
- IPv6 support: excluded from the stated version-one scope.

## RTT and packet-loss statistics

**Decision**: Measure elapsed monotonic time around each probe. Count each sent probe as one attempt; a valid correlated ICMP response is received, and timeout is loss. Compute min/average/max only from successful RTTs and omit them when there are no successes.

**Rationale**: A monotonic clock avoids wall-clock adjustments. Explicit denominators make loss deterministic; omitting empty latency statistics avoids misleading fabricated values.

**Alternatives considered**:
- Include timeout duration as an RTT: rejected because it is not a measured response latency.
- Report zero RTT for an unanswered hop: rejected because zero would be a false measurement.

## CLI and test strategy

**Decision**: Use `argparse`, a fixed-width terminal table rendered without external packages, and `unittest`. Inject or patch socket creation and time measurement in probe tests.

**Rationale**: These are standard-library tools, support the requested command-line experience, and allow test execution without network access or administrator rights.

**Alternatives considered**:
- External table-rendering or test libraries: rejected to keep installation dependency-free.

## References

- Microsoft Learn, [TCP/IP raw sockets](https://learn.microsoft.com/en-us/windows/win32/winsock/tcp-ip-raw-sockets-2): Windows raw ICMP socket support and administrator requirement.
- Python documentation, [socket — Low-level networking interface](https://docs.python.org/3/library/socket.html): standard-library socket and address-resolution APIs.
