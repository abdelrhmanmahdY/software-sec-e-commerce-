# Workflow Evidence Correction

The initial workflow runs `workflow_checks_20261122T053130Z.json` and
`workflow_checks_20261122T053648Z.json` are preserved unchanged.

The 05:31:30 run did not independently verify the stock rejection path. Its
synthetic user's store credit was lower than the attempted cart total, so the
checkout returned `Insufficient store credit` before reaching stock validation.
The 05:36:48 run confirmed that same result and therefore also did not prove
the stock check.

The corrected run, `workflow_checks_20261122T053704Z.json`, supplied sufficient
in-memory credit, observed the cart-add response quantity of 4 for a request
quantity of 3, then observed HTTP 400 with `Insufficient stock for Disposable
test item`. Stock, credit, order count, and cart state were checked afterward.
Only the corrected run supports the stock-validation result.

All three runs used synthetic fixtures and process-local SQLite `:memory:`;
none touched persistent PostgreSQL data.
