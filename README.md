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
| **Retailer APIs** — Best Buy (free), Walmart affiliate (free), eBay Browse (free), Amazon via Keepa (paid) | Direct catalog queries for "sale price ≥70% under regular price" | free/paid key |
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

## Setup for GitHub Actions + Discord (the configured path)

`config.yaml` is committed and already tuned: strict scoring (alert at 80+),
hot-ticket categories only (tech, tools, appliances), Discord alerts, scan
every 10 minutes. You only need to add secrets.

1. **Discord webhook.** In your server: channel → Edit → Integrations →
   Webhooks → New Webhook → Copy URL.
2. **Best Buy key (free, instant).** https://developer.bestbuy.com → sign up →
   the key is emailed to you.
3. **Walmart key (free, ~10 min).** https://walmart.io → create account →
   Affiliate API → create an application. Generate an RSA key pair:
   ```bash
   openssl genrsa -out wm.pem 2048
   openssl rsa -in wm.pem -pubout -out wm_pub.pem   # paste this into the walmart.io app
   ```
   Note the Consumer ID and key version the portal shows.
4. **eBay keys (free, instant).** https://developer.ebay.com → Application
   Keys → Production → copy the App ID (client id) and Cert ID (client secret).
5. **Add repository secrets** at Settings → Secrets and variables → Actions:
   `DISCORD_WEBHOOK_URL`, `BESTBUY_API_KEY`, `WALMART_CONSUMER_ID`,
   `WALMART_PRIVATE_KEY_PEM` (the full contents of `wm.pem`),
   `WALMART_KEY_VERSION` (usually `1`), `EBAY_CLIENT_ID`, `EBAY_CLIENT_SECRET`.
6. Actions tab → **dealbot** → Run workflow. The log shows which sources
   loaded and what scored. From then on it runs itself every 10 minutes.

Missing a key? That source is skipped and everything else still runs.

Amazon needs Keepa, which is a paid API starting around €49/month
(there is no free tier). Flip `keepa.enabled: true` in `config.yaml` and add
`KEEPA_API_KEY` if you subscribe.

## Quick start (local)

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

## Direct retailer scraping: what's feasible

Assessed, not built. The community feeds plus Best Buy/Walmart APIs cover
these retailers already; the unofficial routes below are fragile and against
each site's terms, so they're listed for reference.

| Retailer | Official API | Unofficial route | Verdict |
|---|---|---|---|
| Best Buy | yes, free | — | **done** |
| Walmart | yes, free (affiliate) | — | **done** |
| Amazon | Product Advertising API needs an affiliate account with sales; Keepa is the practical option | page scraping is blocked hard | Keepa (paid) |
| Target | none | `redsky.target.com` JSON that the website uses; needs a public key scraped from site JS, no catalog-wide "sale" query | watchlist-only via JSON-LD on product pages (works) |
| Home Depot | none | internal GraphQL behind Akamai bot protection | watchlist-only via JSON-LD (works for most pages) |
| Lowe's | none | Akamai protected, JSON-LD present | watchlist-only |
| Costco | none | Akamai protected, prices often need login | community feeds only |
| Newegg | affiliate feed (CJ) | JSON-LD present | watchlist-only |
| eBay | Browse API (free key) | — | **done** (new, fixed-price, established sellers only) |

So for Target / Home Depot / Lowe's the honest answer is: there is no way to
sweep their whole catalog for mis-prices without a headless browser farm and
rotating proxies, which is both expensive and a ban-me-please signal. The
community feeds catch their errors within minutes anyway.

## Caveats

- Reddit's public JSON is rate-limited (~10 req/min unauthenticated); the
  default subreddit list and 10-minute interval stay well under that.
- Amazon and Walmart product pages serve bot challenges; use Keepa / the
  Walmart API for those rather than the watchlist.
- A pricing error is only a deal if the retailer honors it. Many cancel.
