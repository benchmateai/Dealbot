"""The visual desk: a local dashboard that tails the event log and shows every move the desk makes.

    python -m dashboard.serve --log-dir logs/data      # then open http://127.0.0.1:8080
    python -m dashboard.export --log-dir logs/data --out data.json   # static snapshot of the same page

Read-only: it never writes to the log, the registry or the broker.
"""
