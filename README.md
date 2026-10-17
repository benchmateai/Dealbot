# Dealbot — pricing-error hunter

Dealbot watches the places pricing mistakes surface first and pings you when
something looks mis-priced: a $399 item listed at $39.99, a 90%-off clearance
glitch, or a post the deal community has already flagged as a price error.

## How it finds errors

Scraping every retailer's full catalog is impractical (bot walls, millions of
SKUs, and it's against most sites' terms). Instead Dealbot combines three
approaches that together cover every major US retailer:

| Approach | Covers | Key needed |
|---|---|---|
| **Community feeds** — r/PriceErrors, r/deals, r/buildapcsales, Slickdeals (front page + live "price error"/"glitch" searches), DealNews, Woot | Everything: Amazon, Walmart, Target, Home Depot, Lowe's, Costco, Best Buy, etc. Mistakes get posted within minutes. | none |
| **Retailer APIs** — Best Buy (free), Walmart affiliate (free), Amazon via Keepa (paid) | Direct catalog queries for "sale price ≥70% under regular price" | free/paid key |
| **Watchlist** — any product URL | Reads the live price from the page's schema.org data (works on Target, Home Depot, Lowe's, Newegg, …) and alerts on a sudden drop | none |

Every deal is scored 0–100 by `dealbot/detector.py`:

- discount depth vs. list price (70% / 85% / 95% tiers)
- decimal-point slips (price ≈ 1/10 or 1/100 of list)
- sub-dollar prices on real items
- price far below the lowest we have seen for that item before
- community language: "price error", "glitch", "mispriced", flair, etc.
- penalties for refurbished, gift-card bundles, expired/dead posts

Scores ≥ 60 (configurable) become alerts. Each item is alerted once, tracked
in a local SQLite file, and tracking params are stripped from URLs so the same
deal from two sources doesn't double-fire.

## Quick start

```bash
pip install -r requirements.txt
cp config.example.yaml config.yaml     # edit thresholds/sources
cp .env.example .env                   # paste webhook URLs / API keys

python -m dealbot sources              # what's enabled?
python -m dealbot run --dry-run        # one pass, print only
python -m dealbot test-notify          # send a fake alert to your channels
python -m dealbot loop                 # run forever, every 10 min
python -m dealbot history              # what has it alerted on
```

With no keys at all, Reddit + Slickdeals + DealNews + Woot run out of the box.

## Notifications

Discord webhook, Slack webhook, Telegram bot, email (SMTP), console. Set the
matching variables in `.env`; any notifier with missing settings is skipped.

## Running it for free on GitHub Actions

`.github/workflows/dealbot.yml` runs a scan every 15 minutes and caches the
SQLite state between runs. Add your webhook/API keys as repository secrets
(Settings → Secrets and variables → Actions) using the names in `.env.example`,
then enable the workflow. GitHub's cron is best-effort and can lag; for
minute-level latency run `dealbot loop` on a small VPS or Raspberry Pi.

## Adding a source

Subclass `dealbot.sources.base.Source`, implement `fetch()` yielding `Deal`
objects, and add it to `REGISTRY` in `dealbot/sources/__init__.py`. Feed-based
sources only need a list of RSS URLs (see `feeds.py`). Parsers are pure
functions so they can be unit-tested with fixtures (see `tests/`).

## Tests

```bash
pip install -r requirements-dev.txt
pytest -q
```

## Caveats

- Reddit's public JSON is rate-limited (~10 req/min unauthenticated); the
  default subreddit list and 10-minute interval stay well under that.
- Amazon and Walmart product pages serve bot challenges; use Keepa / the
  Walmart API for those rather than the watchlist.
- A pricing error is only a deal if the retailer honors it. Many cancel.
