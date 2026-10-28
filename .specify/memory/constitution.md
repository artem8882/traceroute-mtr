<!--
Sync Impact Report
Version change: uninitialized scaffold -> 1.0.0
Modified principles: none
Added principles: Clean, Maintainable Python; Windows Compatibility; Modular Design and Type Hints;
  Safe Network Operations; Automated Unit Tests; Clear README Documentation; Standard Library First;
  Command-Line Interface
Added sections: Additional Constraints; Development Workflow
Removed sections: none
Follow-up TODO: confirm and replace the original ratification date.
-->

# pyroute-mtr Constitution

## Core Principles

### I. Clean, Maintainable Python
Production code MUST use Python 3.11 or newer and favor clear, maintainable implementations.
Changes MUST be understandable and consistent with established project conventions.

### II. Windows Compatibility
The application MUST support Windows as a primary platform. Platform-specific behavior,
including socket permissions and errors, MUST be handled and documented so users can operate
the tool on Windows.

### III. Modular Design and Type Hints
Code MUST be organized into cohesive modules with clear responsibilities. Public functions and
important internal interfaces MUST use type hints to make contracts explicit and maintainable.

### IV. Safe Network Operations
Network operations MUST use bounded timeouts and handle expected socket, resolution, permission,
and network errors without crashing or misreporting successful results. Failures and missing
responses MUST be represented clearly to the user.

### V. Automated Unit Tests
Behavioral changes MUST include automated unit tests. Tests MUST be repeatable and MUST NOT
depend on live network access when network behavior can be isolated or mocked.

### VI. Clear README Documentation
The README MUST document installation, supported requirements, command usage, and relevant
limitations or troubleshooting steps. User-visible behavior changes MUST be reflected in the
documentation.

### VII. Standard Library First
Implementations MUST prefer the Python standard library. Any third-party runtime dependency
MUST have a clear justification and be documented.

### VIII. Command-Line Interface
The application MUST remain usable as a command-line tool. Inputs, results, errors, and exit
behavior MUST be suitable for terminal use and documented through the CLI help and README.

## Additional Constraints

The minimum supported interpreter is Python 3.11. The project MUST preserve Windows support
when selecting APIs or dependencies. Network probing behavior MUST account for operating-system
permissions and network filtering; lack of a reply MUST NOT be presented as proof that a host or
hop is unavailable.

## Development Workflow

Changes MUST include or update tests for affected behavior and documentation for changed
user-facing behavior. Before a change is considered complete, the applicable unit tests MUST
pass. Tests for network behavior MUST use controlled, deterministic inputs rather than requiring
administrator access or sending real packets.

## Governance

This constitution governs project decisions and supersedes conflicting local conventions.
Amendments MUST update this document, explain their impact, and receive review alongside the
change they govern. Changes to principles or scope MUST use the versioning policy below.

Versioning follows semantic versioning: MAJOR for backward-incompatible governance changes or
principle removals/redefinitions; MINOR for new principles or materially expanded requirements;
PATCH for clarifications and non-semantic wording changes. Compliance MUST be reviewed during
feature planning and code review, with applicable tests and documentation used as evidence.

**Version**: 1.0.0 | **Ratified**: TODO(RATIFICATION_DATE): original adoption date unknown | **Last Amended**: 2026-10-28
