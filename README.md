# pyroute-mtr

A Python 3.11+ command-line traceroute utility that sends IPv4 ICMP echo requests with increasing TTL values. It reports responding hop addresses, round-trip time, and packet loss using only Python's standard library at runtime.

## Requirements

- Python 3.11 or newer.
- Windows users must run the command from an **Administrator terminal**. Windows restricts raw ICMP sockets to administrators.
- A network that allows ICMP traffic. Firewalls and routers may block or rate-limit ICMP responses.

## Installation

From the project directory:

```powershell
py -3.11 -m pip install .
```

The package installs the `pyroute-mtr` command. To run directly from a checkout without installing:

```powershell
py -3.11 -m pyroute_mtr example.com
```

## Usage

Open PowerShell or Command Prompt as Administrator on Windows, then run:

```powershell
pyroute-mtr example.com
```

Or specify an IPv4 address and probe settings:

```powershell
pyroute-mtr 1.1.1.1 --count 3 --timeout 1 --max-hops 20
```

| Option | Description | Default |
|---|---|---:|
| `TARGET` | Required hostname or IPv4 address | — |
| `-c`, `--count` | Number of probes sent per hop | `3` |
| `-w`, `--timeout` | Timeout for each probe, in seconds | `1` |
| `-m`, `--max-hops` | Maximum TTL/hop number (1–255) | `30` |
| `-h`, `--help` | Show help and exit | — |

Example table:

```text
Hop  Address      Sent  Recv  Loss   Min ms  Avg ms  Max ms
---  -----------  ----  ----  -----  ------  ------  ------
1    192.0.2.1    3     3     0.0%   1.32    1.48    1.71
2    *            3     0     100.0% -       -       -
3    1.1.1.1      3     3     0.0%   12.01   12.44   12.96
```

RTT statistics include only successful, correlated ICMP responses. Timeouts count as loss; a hop with no responses is shown as `*` and has no latency values. A later hop can respond even when an intermediate hop does not.

## Errors and troubleshooting

- **Permission denied / raw socket could not be created**: On Windows, reopen the terminal using **Run as administrator** and retry.
- **Target could not be resolved**: Check the hostname spelling and DNS/network access. IPv6 literals are not supported; use an IPv4 address or a hostname with an IPv4 DNS record.
- **No replies or high packet loss**: The destination or an intermediate network may filter or rate-limit ICMP. Missing responses do not necessarily indicate that the hop is down.
- **Network errors during probes**: The affected probe is reported to standard error; the trace continues when possible.

## Tests

Run the unit tests from the project root:

```powershell
py -3.11 -m unittest discover -s tests -v
```

All unit tests use mocked sockets and deterministic results; they do not send network packets or require administrator access.
