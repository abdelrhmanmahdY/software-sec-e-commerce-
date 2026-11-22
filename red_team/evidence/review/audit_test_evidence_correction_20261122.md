# Django Test Evidence Correction

The earlier timestamped `audit_tests_*.txt` files are preserved unchanged. They
were zero bytes because the initial runner passed an unsupported output-stream
argument to Django's test runner and did not capture its stderr output. Those
files must not be used as proof of test execution.

The runner now redirects test-runner stdout/stderr and saves the full test
output. `audit_tests_20261122T060013Z.txt` is non-empty and contains the
discovered 16-test run ending in `Ran 16 tests ... OK`. This corrected file is
the evidence used by the final report.
