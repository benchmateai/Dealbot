from dealbot.models import Deal
from dealbot.runner import run_once
from dealbot.sources import REGISTRY
from dealbot.sources.base import Source


class Fake(Source):
    name = "fake"
    calls = 0

    def fetch(self):
        Fake.calls += 1
        yield Deal(title="Sony WH-1000XM5 $39.99 (reg $399.99) price error", url="https://www.amazon.com/dp/B1",
                   source="fake", price=39.99, list_price=399.99)
        yield Deal(title="Normal sale $90 (reg $100)", url="https://www.amazon.com/dp/B2", source="fake",
                   price=90, list_price=100)
        yield Deal(title="dupe", url="https://www.amazon.com/dp/B1?tag=x", source="fake", price=39.99, list_price=399.99)


def test_run_once_dedupes_and_persists(tmp_path, capsys):
    REGISTRY["fake"] = Fake
    cfg = {"db_path": str(tmp_path / "t.db"), "sources": {"fake": {}}, "notifiers": {"console": {}},
           "detector": {}, "max_alerts_per_run": 10}
    res = run_once(cfg)
    assert res.fetched == 3 and res.scored == 2
    assert len(res.alerts) == 1 and res.alerts[0].deal.url.endswith("/B1")
    assert "[" in capsys.readouterr().out

    res2 = run_once(cfg)
    assert res2.alerts == [] and res2.skipped_seen == 1
