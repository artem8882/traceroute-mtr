# Command-Line Contract

## Invocation

```text
pyroute-mtr TARGET [--count COUNT] [--timeout SECONDS] [--max-hops HOPS]
python -m pyroute_mtr TARGET [--count COUNT] [--timeout SECONDS] [--max-hops HOPS]
```

`TARGET` is required and accepts an IPv4 address or resolvable hostname.

| Argument | Meaning | Default |
|---|---|---:|
| `-c`, `--count` | Number of ICMP echo probes sent per hop | 3 |
| `-w`, `--timeout` | Maximum wait per probe, in seconds; must be positive | 1 |
| `-m`, `--max-hops` | Maximum TTL/hop number; must be 1 through 255 | 30 |
| `-h`, `--help` | Show usage and exit | — |

## Output

Successful traces print a terminal table with one row per attempted TTL. Columns include hop number, responder address (or `*` if none), sent/received counts, packet loss, and minimum/average/maximum RTT in milliseconds. RTT columns are `-` when no response was received.

Invalid arguments, unresolved targets, and unrecoverable socket setup errors are explained on standard error and return a nonzero exit status. Per-probe timeouts are represented as loss and do not prevent probing later TTLs. The trace stops after a destination echo reply or at the configured hop limit.

On Windows, raw ICMP socket creation requires an elevated (Administrator) terminal. Permission errors must include that guidance.
