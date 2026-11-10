"""The review gate (ops/review_gate.py): money-code commits go out only with a Reviewed-by: trailer."""

import importlib.util
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("review_gate", ROOT / "ops" / "review_gate.py")
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)


def git(repo, *args):
    return subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True, check=True).stdout.strip()


def commit(repo, path, text, message):
    f = repo / path
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(text)
    git(repo, "add", path)
    git(repo, "-c", "user.name=t", "-c", "user.email=t@example.invalid", "commit", "-q", "-m", message)
    return git(repo, "rev-parse", "HEAD")


def test_the_shipped_money_paths_cover_the_desk_the_broker_and_the_paper_reports():
    pats = gate.patterns()
    assert all(gate.is_money(f, pats) for f in ("broker/paper.py", "kalshi/api.py", "reports/reconcile.py", "lab/strategies/e_desk.py", "dashboard/money.py"))
    assert gate.is_money("lab/gap_pairs.json", pats) and gate.is_money("dashboard/money_page/index.html", pats)  # what fair() prices from; the page's daily P&L
    assert not any(gate.is_money(f, pats) for f in ("ops/TEAM.md", "tests/test_desk.py", "dashboard/static/index.html", "reports/Viable Kalshi trading strategies.md"))


def test_a_money_commit_without_the_trailer_is_refused_and_one_with_it_goes_out(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    git(repo, "init", "-q")
    base = commit(repo, "README.md", "x", "start")
    docs = commit(repo, "ops/notes.md", "y", "notes only")
    money = commit(repo, "broker/paper.py", "fee = 1", "change the fee")
    pats = gate.patterns()
    shas = gate.commits(money, base, cwd=str(repo))
    assert set(shas) == {docs, money}
    bad = gate.unreviewed(shas, pats, cwd=str(repo))
    assert [(b[0], b[2]) for b in bad] == [(money, ["broker/paper.py"])] and "change the fee" in gate.report(bad)
    git(repo, "-c", "user.name=t", "-c", "user.email=t@example.invalid", "commit", "-q", "--amend", "-m",
        "change the fee\n\nReviewed-by: fresh reviewer (subagent), no findings")
    fixed = git(repo, "rev-parse", "HEAD")
    assert gate.unreviewed(gate.commits(fixed, base, cwd=str(repo)), pats, cwd=str(repo)) == []
    assert gate.commits(gate.ZERO, base, cwd=str(repo)) == []  # deleting a branch adds nothing
