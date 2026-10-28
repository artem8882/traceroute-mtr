import contextlib
import io
import unittest

from pyroute_mtr.cli import main, parse_arguments
from pyroute_mtr.probe import HopResult, ProbeResult, TraceError


class CliTests(unittest.TestCase):
    def test_argument_defaults(self):
        args = parse_arguments(["example.com"])

        self.assertEqual(args.target, "example.com")
        self.assertEqual(args.count, 3)
        self.assertEqual(args.timeout, 1.0)
        self.assertEqual(args.max_hops, 30)

    def test_nonpositive_arguments_are_rejected(self):
        for argv in (
            ["example.com", "--count", "0"],
            ["example.com", "--max-hops", "-1"],
            ["example.com", "--max-hops", "256"],
            ["example.com", "--timeout", "0"],
            ["example.com", "--timeout", "inf"],
        ):
            with self.subTest(argv=argv), contextlib.redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit) as raised:
                    parse_arguments(argv)
            self.assertEqual(raised.exception.code, 2)

    def test_main_renders_statistics_table(self):
        hops = [
            HopResult(
                ttl=1,
                probes=[
                    ProbeResult(1, 1, "reply", "192.0.2.1", 4.0, sent=True),
                    ProbeResult(1, 2, "timeout", sent=True),
                ],
            )
        ]
        calls = []

        def fake_trace(target, *, count, timeout, max_hops):
            calls.append((target, count, timeout, max_hops))
            return hops

        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            exit_code = main(
                ["example.com", "--count", "2", "--timeout", "0.5", "--max-hops", "4"],
                trace_function=fake_trace,
            )

        self.assertEqual(exit_code, 0)
        self.assertEqual(calls, [("example.com", 2, 0.5, 4)])
        self.assertIn("Hop", stdout.getvalue())
        self.assertIn("192.0.2.1", stdout.getvalue())
        self.assertIn("50.0%", stdout.getvalue())
        self.assertIn("4.00", stdout.getvalue())

    def test_trace_error_is_explained_on_stderr(self):
        stderr = io.StringIO()

        with contextlib.redirect_stderr(stderr):
            exit_code = main(
                ["invalid.example"],
                trace_function=lambda *args, **kwargs: (_ for _ in ()).throw(
                    TraceError("Unable to resolve target")
                ),
            )

        self.assertEqual(exit_code, 2)
        self.assertIn("Unable to resolve target", stderr.getvalue())

    def test_windows_raw_socket_permission_error_has_elevation_guidance(self):
        stderr = io.StringIO()

        with contextlib.redirect_stderr(stderr):
            exit_code = main(
                ["192.0.2.1"],
                trace_function=lambda *args, **kwargs: (_ for _ in ()).throw(
                    TraceError(
                        "Could not create ICMP raw socket. Run this command in an "
                        "Administrator terminal."
                    )
                ),
            )

        self.assertEqual(exit_code, 2)
        self.assertIn("Administrator", stderr.getvalue())

    def test_probe_network_errors_are_reported_but_trace_table_is_printed(self):
        hops = [
            HopResult(
                ttl=1,
                probes=[
                    ProbeResult(
                        1,
                        1,
                        "network_error",
                        detail="network unreachable",
                    )
                ],
            )
        ]
        stdout = io.StringIO()
        stderr = io.StringIO()

        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            exit_code = main(["192.0.2.1"], trace_function=lambda *a, **k: hops)

        self.assertEqual(exit_code, 0)
        self.assertIn("Hop", stdout.getvalue())
        self.assertIn("network unreachable", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
