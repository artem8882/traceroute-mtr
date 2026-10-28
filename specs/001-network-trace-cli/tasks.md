---
description: "Task list for the Network Trace CLI"
---

# Tasks: Network Trace CLI

**Input**: Design documents from `specs/001-network-trace-cli/`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/cli.md`, and `quickstart.md`

**Tests**: Unit tests are explicitly required. Add deterministic `unittest` cases with mocked sockets and controlled probe results; do not require live network or administrator access to run them.

**Organization**: Tasks are grouped by user story so each increment can be implemented and verified independently.

## Phase 1: Setup

**Purpose**: Establish a dependency-free importable Python CLI project.

- [X] T001 Create `pyproject.toml` for Python 3.11+, standard-library-only packaging, the `pyroute-mtr` console entry point, and `tests/__init__.py` for focused unittest module invocations.
- [X] T002 Create the `pyroute_mtr/__init__.py` and `pyroute_mtr/__main__.py` package entry files.

---

## Phase 2: Foundational

**Purpose**: Define shared probe and hop result shapes in `pyroute_mtr/probe.py` so the tracing, statistics, and CLI layers use the same outcomes.

- [X] T003 Define typed probe and hop result records in `pyroute_mtr/probe.py`, including TTL, sequence, responder, RTT, outcome, error detail, and destination-reached state.

**Checkpoint**: Shared result records are established; user-story work can proceed.

---

## Phase 3: User Story 1 - Trace a route to a destination (Priority: P1)

**Goal**: Send correlated IPv4 ICMP echo probes with increasing TTLs, report responding hops, and stop on destination response or the configured hop limit.

**Independent Test**: Run `python -m unittest tests.test_probe -v`; controlled sockets verify TTL progression, ICMP packet correlation, timeouts, later responding hops after an unanswered hop, and destination stopping without sending live packets.

### Tests for User Story 1

- [X] T004 [P] [US1] Add mocked-socket tests for ICMP packet creation/parsing, TTL progression, unmatched replies, timeout behavior, and destination detection in `tests/test_probe.py`.

### Implementation for User Story 1

- [X] T005 [US1] Implement IPv4 resolution, ICMP echo packet creation/checksum, TTL-specific probing, correlated ICMP response parsing, timeout handling, and trace progression in `pyroute_mtr/probe.py`.

**Checkpoint**: Controlled probe results show hops in order and stop only when the destination replies or the hop limit is reached.

---

## Phase 4: User Story 2 - Assess hop quality (Priority: P2)

**Goal**: Calculate sent/received counts, packet loss, and successful RTT minimum, average, and maximum values for each hop.

**Independent Test**: Run `python -m unittest tests.test_statistics -v`; known reply and timeout sequences produce exact counts, loss percentages, and RTT statistics, while unanswered hops have no fabricated RTT values.

### Tests for User Story 2

- [X] T006 [P] [US2] Add `unittest` coverage for complete replies, mixed replies/timeouts, all-timeout hops, and exact RTT min/average/max values in `tests/test_statistics.py`.

### Implementation for User Story 2

- [X] T007 [US2] Implement hop-statistics aggregation from probe results in `pyroute_mtr/statistics.py`, with loss based on attempts sent and RTT values based only on valid replies.

**Checkpoint**: All hop statistics match the independently calculated values for controlled probe outcomes.

---

## Phase 5: User Story 3 - Understand and recover from failures (Priority: P3)

**Goal**: Provide a usable argparse CLI, readable terminal table, clear errors, and Windows setup and usage guidance.

**Independent Test**: Run `python -m unittest tests.test_cli -v` to verify valid and invalid arguments, rendered table values, destination resolution errors, and socket permission failures without live network access; follow `README.md` to install and run the tool on Windows.

### Tests for User Story 3

- [X] T008 [P] [US3] Add CLI tests for argument defaults and validation, table output, resolution failures, recoverable probe errors, and actionable raw-socket permission messages in `tests/test_cli.py`.

### Implementation for User Story 3

- [X] T009 [US3] Implement argparse options, orchestration, terminal-table rendering, stderr errors, and exit statuses in `pyroute_mtr/cli.py`.
- [X] T010 [US3] Document Python installation, elevated Windows terminal requirement, direct and installed invocation, examples, options, output, timeout, and network error behavior in `README.md`.

**Checkpoint**: Users can run the packaged or module CLI and understand its table, errors, and Windows privilege requirements.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Verify the full implementation and packaging contract.

- [X] T011 Run `python -m unittest discover -s tests -v` and `python -m pyroute_mtr --help`; fix failures in the relevant source or test files.
- [X] T012 Validate the quickstart commands and expected output documentation in `specs/001-network-trace-cli/quickstart.md` and `README.md`.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies.
- **Foundational (Phase 2)**: Depends on Setup.
- **User Stories (Phases 3–5)**: Depend on the shared result records; implement in priority order for the MVP.
- **Polish (Phase 6)**: Depends on all desired stories being complete.

### User Story Dependencies

- **US1 (P1)**: Depends on Setup and Foundational; no dependency on another story.
- **US2 (P2)**: Depends on shared probe result records; the statistics module is independently testable.
- **US3 (P3)**: Integrates probing and statistics to provide the end-user CLI.

### Parallel Opportunities

- T004 and T006 are separate test files and can be authored in parallel after T003.
- T008 can be authored after the package skeleton and independently of the statistics implementation.
- Probe tests and statistics tests require no live network access.

## Parallel Example: User Story Tests

```text
Task: T004 tests/test_probe.py
Task: T006 tests/test_statistics.py
```

## Implementation Strategy

Deliver the tracing engine as the P1 MVP, then add correct per-hop statistics, then complete CLI error handling and README guidance. Finish by running the entire standard-library test suite and checking the documented help/invocation paths.
