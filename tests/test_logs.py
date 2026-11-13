import json
import math

import pytest

from logs import REDACTED, LogSchemaError, LogWriter, Redactor, read_events
from tests.helpers import T0

SECRET = "a" * 64


def test_redactor_removes_values_patterns_and_secret_keys():
    r = Redactor([SECRET, "short"])
    record = {
        "note": f"token {SECRET} inside",
        "nested": [{"Authorization": "Bearer abcdefghijklmnop"}, "sk-ABCDEFGHIJKLMNOPQRSTUVWXYZ12", "x" * 10],
        "desk_secret": "anything at all",
        "hex": "deadbeef" * 6,
        "fine": "short values stay",
        "tokens": 123,
        "usage": {"input_tokens": 456, "access_token": "abcdefghijklmnop"},
    }
    out = r.redact(record)
    assert SECRET not in json.dumps(out)
    assert out["note"] == f"token {REDACTED} inside"
    assert out["nested"][0]["Authorization"] == REDACTED
    assert out["nested"][1] == REDACTED and out["nested"][2] == "x" * 10
    assert out["desk_secret"] == REDACTED and out["hex"] == REDACTED and out["fine"] == "short values stay"
    assert out["tokens"] == 123 and out["usage"]["input_tokens"] == 456 and out["usage"]["access_token"] == REDACTED


def test_writer_appends_jsonl_per_day_with_redaction_and_clean_floats(tmp_path):
    with LogWriter(tmp_path, Redactor([SECRET])) as log:
        rec = log.write("heartbeat", {"blk": 1, "equity_usd": math.nan, "note": SECRET, "tup": (1, 2)}, ts_ms=T0)
        log.write("heartbeat", {"blk": 2}, ts_ms=T0 + 86_400_000)
        with pytest.raises(LogSchemaError):
            log.write("veto", {"decision_id": "d"})
        with pytest.raises(LogSchemaError):
            log.write("not_a_kind", {})
        with pytest.raises(LogSchemaError):
            log.write("heartbeat", {"blk": 3, "ts": 1})
    assert rec["equity_usd"] is None and rec["note"] == REDACTED and rec["tup"] == [1, 2] and rec["kind"] == "heartbeat"
    files = sorted(p.name for p in tmp_path.glob("events-*.jsonl"))
    assert files == ["events-2023-11-14.jsonl", "events-2023-11-15.jsonl"]
    events = list(read_events(tmp_path))
    assert [e["blk"] for e in events] == [1, 2]
    assert [e["blk"] for e in read_events(tmp_path, date="2023-11-15")] == [2]
    assert list(read_events(tmp_path, kinds=("veto",))) == []


def test_a_copy_taken_mid_write_reads_up_to_the_last_complete_line(tmp_path):
    import json

    import pytest

    from logs.writer import read_events

    path = tmp_path / "events-2026-11-03.jsonl"
    path.write_text(json.dumps({"kind": "heartbeat", "ts": 1}) + "\n" + '{"kind": "heartbe')
    assert [e["ts"] for e in read_events(tmp_path)] == [1]
    path.write_text('{"kind": "heartbe\n' + json.dumps({"kind": "heartbeat", "ts": 2}) + "\n")
    with pytest.raises(json.JSONDecodeError):
        list(read_events(tmp_path))  # damage anywhere but the end is still an error
