# Data Model: Network Trace CLI

The application keeps all data in memory for one trace.

## Trace configuration

| Field | Type | Constraints |
|---|---|---|
| target | string | Required hostname or IPv4 literal |
| destination_ipv4 | IPv4 address string | Resolved once before probing |
| probe_count | integer | Positive; default 3 |
| timeout_seconds | number | Positive; default 1 second |
| max_hops | integer | 1 through 255; default 30 |

## Probe result

Represents one attempt sent at one TTL.

| Field | Type | Constraints |
|---|---|---|
| ttl | integer | 1 through configured maximum |
| sequence | integer | Unique within the trace |
| responder_ipv4 | IPv4 address string or absent | Present only when a correlated ICMP reply is received |
| rtt_ms | number or absent | Present only for a valid received reply; measured with a monotonic clock |
| outcome | `reply`, `timeout`, or `network_error` | Exactly one outcome per attempted probe |
| sent | boolean | True only if the echo request was successfully sent |
| detail | string or absent | Network error context for a failed attempt |
| reached_destination | boolean | True only for an echo reply from the selected destination |

## Hop result

Summarizes all probes at one TTL.

| Field | Type | Constraints |
|---|---|---|
| ttl | integer | Unique, increasing within a trace |
| probes | list of probe results | Contains the configured number of attempts unless an unrecoverable trace-level error stops execution |
| responder_ipv4 | IPv4 address string or absent | First responding address observed at this TTL |
| sent_count | integer | Number of attempts actually sent |
| received_count | integer | Number of valid ICMP replies observed |
| packet_loss_percent | number | `(sent_count - received_count) / sent_count * 100`; absent if no attempts were sent |
| min_rtt_ms | number or absent | Minimum successful RTT |
| average_rtt_ms | number or absent | Arithmetic mean of successful RTTs |
| max_rtt_ms | number or absent | Maximum successful RTT |
| reached_destination | boolean | True if any correlated echo reply came from the resolved destination |

## Trace state

The trace progresses through destination resolution, probing TTL values from 1 through `max_hops`, and completion. Completion occurs when the destination replies or the hop limit is reached. Unanswered hops do not stop later TTL probes. A destination-resolution failure or raw-socket setup failure aborts before any hop results are produced.
