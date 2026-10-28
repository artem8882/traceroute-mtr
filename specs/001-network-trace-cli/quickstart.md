# Quickstart: Network Trace CLI

## Prerequisites

- Python 3.11 or newer.
- Windows: an elevated terminal (Run as Administrator) to create the raw ICMP socket.
- Network access that permits outbound ICMP echo and inbound ICMP responses.

## Install from a local checkout

From the project root:

```powershell
py -3.11 -m pip install .
```

Alternatively, run directly without installation:

```powershell
py -3.11 -m pyroute_mtr example.com
```

## Validate

Run the unit tests; they use controlled probe behavior and do not send packets:

```powershell
py -3.11 -m unittest discover -s tests -v
```

Run a short live trace from an elevated terminal:

```powershell
py -3.11 -m pyroute_mtr 1.1.1.1 --count 2 --timeout 1 --max-hops 5
```

Expected output is a terminal table with rows ordered from TTL 1 through the destination or configured limit. An unanswered hop is marked `*`; latency fields are absent for hops with no responses. Network filtering or missing ICMP responses can result in packet loss even when later hops respond.

See [the CLI contract](contracts/cli.md) for arguments and error behavior, and [the data model](data-model.md) for statistics definitions.
