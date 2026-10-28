# Implementation Plan: Network Trace CLI

**Branch**: `001-network-trace-cli` | **Date**: 2026-10-28 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/001-network-trace-cli/spec.md` and implementation constraints supplied by the user.

## Summary

Build a dependency-free Python 3.11+ IPv4 ICMP echo traceroute CLI. Send echo requests with an increasing IPv4 TTL, receive ICMP replies, and report each hop's address, probe loss, and successful RTT min/average/max in a terminal table. Keep raw network I/O, statistics, and CLI presentation in separate modules; expose deterministic unit-test seams so tests require no live network.

## Technical Context

**Language/Version**: Python 3.11+

**Primary Dependencies**: Python standard library only (`socket`, `struct`, `time`, `argparse`, `statistics`, `ipaddress`, and `unittest`)

**Storage**: N/A; a trace is transient and no history is persisted.

**Testing**: `python -m unittest discover -s tests -v`, with sockets and clocks replaced by controlled fakes/mocks for unit tests.

**Target Platform**: Windows first; IPv4 hostname and numeric IPv4 address destinations.

**Project Type**: Single Python CLI package.

**Performance Goals**: Complete each configured probe within its timeout; defaults are three probes per hop, a one-second timeout, and 30 hops.

**Constraints**: No third-party runtime dependencies. Raw ICMP sockets require administrator privileges on Windows; fail with actionable guidance if socket creation is denied. Keep probe, statistics, and CLI code in distinct modules. Unit tests must not require network access or elevated privileges.

**Scale/Scope**: One bounded foreground trace, human-readable terminal table, no continuous mode, persistence, IPv6, or machine-readable output in this version.

## Constitution Check

The checked-in constitution contains only unfilled template placeholders; it defines no ratified principles or enforceable gates. The implementation therefore follows the explicit feature requirements and standard project quality gates: standard-library-only runtime, modular code, deterministic unit tests, clear CLI errors, and Windows documentation.

**Pre-design gate**: PASS — no applicable constitution rules are present to violate.

## Project Structure

### Documentation (this feature)

```text
specs/001-network-trace-cli/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── cli.md
└── tasks.md
```

### Source Code (repository root)

```text
pyroute_mtr/
├── __init__.py
├── __main__.py
├── cli.py
├── probe.py
└── statistics.py

tests/
├── test_cli.py
├── test_probe.py
└── test_statistics.py

pyproject.toml
README.md
```

**Structure Decision**: Use one importable `pyroute_mtr` package with separate ICMP probing, summary statistics, and argparse/table CLI modules. `__main__.py` supports `python -m pyroute_mtr`; a `pyproject.toml` console-script entry point supports installation as `pyroute-mtr`. Keep the test suite in standard-library `unittest`.

## Constitution Check (Post-Design)

- Runtime uses only the standard library: PASS.
- Probe, statistics, and CLI are separated and independently testable: PASS.
- Tests cover core behavior without live network access: PASS.
- Windows raw-socket privilege limitation is surfaced and documented: PASS.

No constitution violations or complexity exceptions apply.
