# Kalshi interfaces: implementation reference for the market-data recorder

Compiled 2026-11-03 (UTC) for a read-only market-data recorder. Nothing here is about placing orders.

**Sources** (all fetched 2026-11-03 between 20:21 and 20:28 UTC; request log in Appendix A):

- docs.kalshi.com: `llms-full.txt` (every page, including the API changelog), `asyncapi.yaml` (Predictions WebSocket spec, `info.version: 2.0.0`), `openapi.yaml` (Predictions REST spec, `info.version: 3.35.0`).
- help.kalshi.com (Intercom): articles 13823851 "Liquidity Incentive Program", 16076644 "Liquidity Incentive Programs: Where to Find Them", 15410219 "Liquidity Provider Program", 13823819 "How to Become a Market Maker on Kalshi" and 13823805 "Fees".
- Live public GETs to `https://api.elections.kalshi.com/trade-api/v2`, plus one WebSocket handshake sent without credentials.

**Conventions**

- `>` blockquotes are Kalshi's exact wording. The source page follows in brackets.
- **INFERRED** means the point is my reading and Kalshi does not state it. **UNCONFIRMED** means I could not verify it from the allowed sources.
- Prices are fixed-point dollar strings and contract counts are fixed-point strings. Parse both with `decimal.Decimal`, never `float`.

---

## 0. One-screen summary

| Topic | Value |
|---|---|
| Production WS URL | `wss://external-api-ws.kalshi.com/trade-api/ws/v2` (recommended). `wss://api.elections.kalshi.com/trade-api/ws/v2` is also supported. |
| Auth | Required for the handshake, even for public channels. A handshake without credentials got **HTTP 401** `{"code":"token_authentication_failure","message":"token authentication failure"}` (tested 2026-11-03). |
| Headers | `KALSHI-ACCESS-KEY`, `KALSHI-ACCESS-TIMESTAMP` (ms), `KALSHI-ACCESS-SIGNATURE` (base64) |
| Signed string | `str(ms_timestamp) + "GET" + "/trade-api/ws/v2"` |
| Signature | RSA keys: RSA-PSS, SHA-256, MGF1(SHA-256), salt = digest length (32). Ed25519 keys: plain Ed25519 over the same string. |
| Market-data channels | `orderbook_delta` (snapshot and deltas, sequenced), `ticker` (no `seq`), `trade` (sequenced), `market_lifecycle_v2` (all markets, sequenced), `cfbenchmarks_value` (about 1/s with 60 s averages, sequenced), `cfbenchmarks_value_5hz` (up to 5/s, sequenced). `ticker_v2` was removed on 2026-02-12. |
| Gap on `orderbook_delta` | Send `update_subscription` with `action: get_snapshot` for **all** subscribed markets, or `unsubscribe`, wait for `unsubscribed`, then `subscribe` again. |
| Keep-alive | The server sends a Ping every 10 s with body `heartbeat`. The client answers with a Pong. |
| Limits | 200 concurrent WS connections **per user** (Basic, Advanced, Expert), shared with Perps. 500k market subscriptions per session. 10k commands/s. 64 MiB maximum message size. One `orderbook_delta` subscription per connection. |
| Units | `*_dollars` are dollar strings with 4 decimals. `*_fp` are contract counts with 2 decimals. `dollar_volume` and `dollar_open_interest` are integer whole dollars. CF values are USD strings with 8 decimals. Incentive `period_reward` is an integer in **centi-cents** (1 = $0.0001). |
| Must set | `use_yes_price` explicitly on `orderbook_delta`. Kalshi will flip its default later. |

---

# Part 1. WebSocket market-data API

## 1.1 Endpoints

| Environment | Recommended WS URL | Also supported |
|---|---|---|
| Production | `wss://external-api-ws.kalshi.com/trade-api/ws/v2` | `wss://api.elections.kalshi.com/trade-api/ws/v2` |
| Demo | `wss://external-api-ws.demo.kalshi.co/trade-api/ws/v2` | `wss://demo-api.kalshi.co/trade-api/ws/v2` |

> WebSocket connections use the same API key authentication and signing path as before. Only the hostname changes for the dedicated Trade API path. [websockets]

Related hosts the recorder should **not** use for market data:

- `wss://warp-ws.kalshi.com/trade-api/ws/v2` (added 2026-10-29). It serves only `fill` and `user_orders`. "Subscribing to any other channel returns error code 8 (`Unknown channel name`)".
- `wss://external-feeds.kalshi.com/trade-api/v2/external-feeds` ("External Feeds WebSocket"). It is signed as `GET /trade-api/v2/external-feeds`. Its contents are not documented anywhere I could find (**UNCONFIRMED**). The AsyncAPI places `cfbenchmarks_value` and `pyth_value` on the normal Trade API socket.
- The Perps (margin) WebSocket at `wss://external-api-margin-ws.kalshi.com/trade-api/ws/v2/margin` has its own spec (`perps_asyncapi.yaml`). It is out of scope here.

REST base URLs, for any REST calls the recorder makes: `https://external-api.kalshi.com/trade-api/v2` is recommended and `https://api.elections.kalshi.com/trade-api/v2` is also supported.

## 1.2 Authentication

> Authentication is required to establish the connection; include API key headers during the WebSocket handshake. Some channels carry only public market data, but the connection itself still requires authentication. [websockets/websocket-connection, also the AsyncAPI `root` channel]

**Does any channel work without authentication? No.** The connection cannot be opened without a key. My one handshake without credentials to `wss://api.elections.kalshi.com/trade-api/ws/v2` (2026-11-03 20:27:17 UTC) returned `HTTP/1.1 401 Unauthorized` with the body `{"code":"token_authentication_failure","message":"token authentication failure"}`.

Once connected, the Quick Start sorts channels into two groups:

> * **Private channels (user-specific data):** `orderbook_delta`, `fill`, `market_positions`, `communications`, `order_group_updates`
> * **Public market-data channels (no additional channel-level auth):** `ticker`, `trade`, `market_lifecycle_v2`, `multivariate_market_lifecycle`, `multivariate` [getting_started/quick_start_websockets]

(`multivariate` was removed on 2026-08-06; see Part 3. The CF Benchmarks and Pyth channel pages each say "Requires authentication.")

**Headers** [quick_start_websockets, api_keys]:

```
KALSHI-ACCESS-KEY: your_api_key_id
KALSHI-ACCESS-SIGNATURE: request_signature
KALSHI-ACCESS-TIMESTAMP: unix_timestamp_in_milliseconds
```

**What is signed:**

> 1. **Create the message to sign:**
>    ```
>    timestamp + "GET" + "/trade-api/ws/v2"
>    ```
> [quick_start_websockets]

> The signature is the base64 encoding of the signed concatenation of the timestamp, the HTTP method and the path. Ed25519 keys sign the string directly; RSA keys use RSA-PSS with SHA-256 (MGF1 with SHA-256, salt length equal to the digest length). [getting_started/api_keys]

> The host does not change the signature payload. Sign the full request path from the API root, without query parameters. [getting_started/api_environments]

Key types: Ed25519 is "recommended" and RSA 2048-bit is still supported. Both were added or confirmed on 2026-09-24.

> The PEM header does not identify the key type: PKCS#8 RSA keys, including `openssl genpkey` output, also begin with `-----BEGIN PRIVATE KEY-----`. Determine the type from the parsed key, as the samples below do. [api_keys]

The repository's `kalshi/auth.py` signs RSA-PSS with `salt_length=PSS.DIGEST_LENGTH`, which matches the docs. It does **not** handle Ed25519 keys.

A minimal handshake header builder, following the docs' sample:

```python
import base64, time
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

def ws_headers(key_id: str, private_key) -> dict:
    ts = str(int(time.time() * 1000))
    msg = (ts + "GET" + "/trade-api/ws/v2").encode()
    if isinstance(private_key, Ed25519PrivateKey):
        sig = private_key.sign(msg)
    else:
        sig = private_key.sign(msg, padding.PSS(mgf=padding.MGF1(hashes.SHA256()),
                                                salt_length=padding.PSS.DIGEST_LENGTH), hashes.SHA256())
    return {"KALSHI-ACCESS-KEY": key_id, "KALSHI-ACCESS-SIGNATURE": base64.b64encode(sig).decode(),
            "KALSHI-ACCESS-TIMESTAMP": ts}
# websockets.connect(url, additional_headers=ws_headers(...))   # as in Kalshi's sample
```

Each reconnect needs a fresh timestamp and signature (**INFERRED**). How far the timestamp may drift from server time is **UNCONFIRMED**; the docs do not say.

Subaccount-restricted API keys can open WebSocket sessions since 2026-07-23. `orderbook_delta` "still delivers the full book".

## 1.3 Message envelope (all messages)

| Field | Meaning |
|---|---|
| `id` | Client command id, echoed on responses. "Generated by the client and should be unique within a WS session… If the id is set to 0, the server treats it the same way as if there was no id." |
| `type` | Message type: `subscribed`, `unsubscribed`, `ok`, `error`, `orderbook_snapshot`, `orderbook_delta`, `ticker`, `trade`, `market_lifecycle_v2`, `event_lifecycle`, `event_fee_update`, `cfbenchmarks_value`, and so on. |
| `sid` | Server-assigned subscription id, minimum 1. |
| `seq` | "Sequential number that should be checked if you want to guarantee you received all the messages. Used for snapshot/delta consistency" (minimum 1). It is present on sequenced channels only. |
| `msg` | Payload object. In the `list_subscriptions` reply it is an array. |
| `sending_ts_ms` | "Unix timestamp in milliseconds when Kalshi queued this message at the network layer." Added to WS messages on 2026-10-01. |

Forward compatibility:

> A channel can gain new message types, and a message new fields. Ignore any message `type` or field your client doesn't recognize instead of treating it as an error. [websockets]

Ordering after a subscribe:

> The acknowledgement continues to precede subscription data. [changelog 2026-09-17]

## 1.4 Commands and responses

All commands have the form `{"id": <int>, "cmd": "<command>", "params": {...}}`.

### subscribe

`params.channels` is required. It takes one or more of `orderbook_delta`, `ticker`, `trade`, `fill`, `market_positions`, `market_lifecycle_v2`, `multivariate_market_lifecycle`, `communications`, `order_group_updates`, `user_orders`, `cfbenchmarks_value`, `cfbenchmarks_value_5hz` and `pyth_value`.

| Param | Applies to | Notes (from the AsyncAPI) |
|---|---|---|
| `market_ticker` / `market_tickers` | market channels | "mutually exclusive" |
| `market_id` / `market_ids` | `ticker` only | UUIDs |
| `send_initial_snapshot` | `ticker` | "If true, receive an initial snapshot for requested market tickers on the ticker channel" (default false) |
| `skip_ticker_ack` | all | "If true, OK responses omit the market_tickers/market_ids lists for this subscription" |
| `use_yes_price` | `orderbook_delta` | See 1.5.1. Default false, and the default will flip. |
| `update_interval_ms` | `orderbook_delta` | `0` (default, real time), `100` or `1000` (conflated). See 1.5.1. |
| `index_ids` | `cfbenchmarks_value`, `cfbenchmarks_value_5hz` | e.g. `["BRTI","ETHUSD_RTI"]` or `["all"]` |
| `underlying_tickers` | `pyth_value` | |
| `user_filter`, `shard_factor`, `shard_key` | `communications` | |

Kalshi's examples, converted to JSON:

```json
{"id": 1, "cmd": "subscribe", "params": {"channels": ["orderbook_delta"], "market_ticker": "CPI-22DEC-TN0.1"}}
{"id": 16, "cmd": "subscribe", "params": {"channels": ["orderbook_delta"], "market_tickers": ["FED-23DEC-T3.00", "CORIVER-2024-T1030"], "update_interval_ms": 100}}
{"id": 2, "cmd": "subscribe", "params": {"channels": ["orderbook_delta", "ticker"], "market_tickers": ["FED-23DEC-T3.00", "CORIVER-2024-T1030"]}}
{"id": 7, "cmd": "subscribe", "params": {"channels": ["ticker"], "market_tickers": ["FED-23DEC-T3.00"], "send_initial_snapshot": true}}
{"id": 5, "cmd": "subscribe", "params": {"channels": ["market_lifecycle_v2"]}}
{"id": 9, "cmd": "subscribe", "params": {"channels": ["cfbenchmarks_value"], "index_ids": ["BRTI", "ETHUSD_RTI"]}}
{"id": 11, "cmd": "subscribe", "params": {"channels": ["cfbenchmarks_value_5hz"], "index_ids": ["BRTI"]}}
```

Response:

```json
{"id": 1, "type": "subscribed", "sending_ts_ms": 1669149841234, "msg": {"channel": "orderbook_delta", "sid": 1}}
```

**INFERRED:** a multi-channel subscribe returns one `subscribed` per channel, each with its own `sid`. The `list_subscriptions` example shows one sid per channel. Keep a `sid → channel` map from these responses.

Repeated subscribes:

> Repeated subscriptions on the same WebSocket call will no longer error. If passing the same market tickers as before, no action will be taken. If passing new market tickers, they will be added to your existing subscription. [changelog 2025-09-25]

### unsubscribe

```json
{"id": 124, "cmd": "unsubscribe", "params": {"sids": [1, 2]}}
```

Response (note that it carries `seq`):

```json
{"id": 102, "sid": 2, "seq": 7, "type": "unsubscribed", "sending_ts_ms": 1669149841234}
```

### update_subscription

Target exactly one subscription, with either `sid: <int>` or `sids: [<int>]` ("Either sid or sids must be provided, not both"). `params.action` is required.

Market channels take `add_markets`, `delete_markets` and `get_snapshot` (orderbook only):

```json
{"id": 124, "cmd": "update_subscription", "params": {"sids": [456], "market_tickers": ["NEW-MARKET-1", "NEW-MARKET-2"], "action": "add_markets"}}
{"id": 125, "cmd": "update_subscription", "params": {"sids": [456], "market_tickers": ["MARKET-TO-REMOVE-1", "MARKET-TO-REMOVE-2"], "action": "delete_markets"}}
{"id": 127, "cmd": "update_subscription", "params": {"sids": [456], "market_tickers": ["MARKET-1", "MARKET-2"], "action": "get_snapshot"}}
{"id": 126, "cmd": "update_subscription", "params": {"sid": 456, "market_tickers": ["NEW-MARKET-3", "NEW-MARKET-4"], "action": "add_markets"}}
```

For `get_snapshot`:

> Only `market_tickers` is supported (not `market_ticker`, `market_id`, or `market_ids`). [changelog 2026-04-20]

`update_subscription` also accepts `send_initial_snapshot` ("for newly added market tickers on the ticker channel").

Response to add and delete:

```json
{"id": 123, "sid": 456, "seq": 222, "type": "ok", "sending_ts_ms": 1669149841234, "msg": {"market_tickers": ["MARKET-1", "MARKET-2", "MARKET-3"]}}
```

(`msg.market_tickers` is the "Full list of market tickers after update"; `skip_ticker_ack` omits it.)

CF Benchmarks subscriptions take `subscribe_indices`, `unsubscribe_indices` and `indexlist`:

```json
{"id": 2, "cmd": "update_subscription", "params": {"sid": 1, "action": "indexlist"}}
{"id": 3, "cmd": "update_subscription", "params": {"sid": 1, "action": "subscribe_indices", "index_ids": ["BRTI"]}}
{"id": 4, "cmd": "update_subscription", "params": {"sid": 1, "action": "unsubscribe_indices", "index_ids": ["BRTI"]}}
{"id": 5, "cmd": "update_subscription", "params": {"sid": 1, "action": "subscribe_indices", "index_ids": ["all"]}}
```

Index updates are answered by `{"type":"ok","id":…,"sid":…,"seq":…,"msg":{"index_ids":[…]}}`, which is the "Current CF Benchmarks index filter after an update; all-mode is ["all"]". `indexlist` is answered by a `cfbenchmarks_value_indexlist` message (section 1.5.5).

### list_subscriptions

```json
{"id": 3, "cmd": "list_subscriptions"}
```

Response:

```json
{"id": 3, "type": "ok", "sending_ts_ms": 1669149841234, "msg": [{"channel": "orderbook_delta", "sid": 1}, {"channel": "ticker", "sid": 2}, {"channel": "fill", "sid": 3}]}
```

### error

```json
{"id": 123, "type": "error", "sending_ts_ms": 1669149841234, "msg": {"code": 7, "msg": "Unknown subscription ID"}}
```

Subscription-scoped errors also carry `sid`, and on sequenced channels `seq`. Codes from the AsyncAPI that matter to a recorder:

| Code | Meaning | Recorder action |
|---|---|---|
| 1 | Unable to process message (bad JSON or wrong field types) | bug |
| 2, 3, 4, 5, 12, 14, 15 | missing params, channels, sids, action or market ticker; unknown cmd | bug |
| 7 | Unknown subscription ID | resync the sid map with `list_subscriptions` |
| 8 | Unknown channel name | bug, or wrong host (warp-ws) |
| 9 | Authentication required: "The requested channel or action requires authentication or channel access that was not granted." | check the key or entitlement |
| 10 | Channel error. **Terminal**: "the user must resubscribe" | resubscribe |
| 11 | Invalid parameter, or `update_interval_ms` differs from the existing orderbook subscription | fix the request |
| 13 | Unsupported action | bug |
| 18 | Command timeout | retry |
| 24 | Index IDs required (CF channels) | bug |
| 25 | Subscription buffer overflow. **Terminal** | resubscribe, read faster, subscribe to fewer markets |
| 26 | Subscription market limit exceeded | split across connections |
| 27 | Too many requests (per-subscription command rate limit) | slow down commands |
| 29 | `update_interval_ms must be 0, 100 or 1000` | bug |

Codes 6, 16 and 17 are retired. The Quick Start error table omits 23, 24 and 26–29; the AsyncAPI lists them.

## 1.5 Channels

### 1.5.1 `orderbook_delta` (message types `orderbook_snapshot` and `orderbook_delta`)

Requirements, verbatim from the AsyncAPI channel description:

> - Authentication required
> - Market specification required:
>   - Use `market_ticker` (string) for a single market
>   - Use `market_tickers` (array of strings) for multiple markets
>   - `market_id`/`market_ids` are not supported for this channel
> - Sends `orderbook_snapshot` first, then incremental `orderbook_delta` updates
> - Supports `update_subscription` with `add_markets` / `delete_markets` / `get_snapshot` actions
> - `get_snapshot` returns an `orderbook_snapshot` for the requested `market_tickers` without changing the subscribed markets. Apply every returned snapshot as a replacement for that market's local book
> - Each connection has one `orderbook_delta` subscription. A repeated `subscribe` adds new markets to its existing `sid`; it does not resend snapshots for markets already subscribed

#### Snapshot example (AsyncAPI)

```json
{
  "type": "orderbook_snapshot",
  "sending_ts_ms": 1669149841234,
  "sid": 2,
  "seq": 2,
  "msg": {
    "market_ticker": "FED-23DEC-T3.00",
    "market_id": "9b0f6b43-5b68-4f9f-9f02-9a2d1b8ac1a1",
    "clock": 4182057,
    "yes_dollars_fp": [["0.0800", "300.00"], ["0.2200", "333.00"]],
    "no_dollars_fp": [["0.5400", "20.00"], ["0.5600", "146.00"]]
  }
}
```

| Field | Type / unit | Notes |
|---|---|---|
| `id` | int | "Present when replying to a get_snapshot command with an ID" |
| `msg.market_ticker`, `msg.market_id` | string, UUID | required |
| `msg.clock` | int64 ≥ 0 | "Exchange clock of the newest change this snapshot includes, or 0 if the market has no recorded change. The snapshot includes every change to this market with a clock at or below this one, and none above it." |
| `msg.yes_dollars_fp` | array of `[price_dollars, count_fp]` string pairs | "Optional - This key will not exist if there are no Yes offers in the orderbook." These are YES **bids**. |
| `msg.no_dollars_fp` | same | NO bids. Absent if empty. Priced in no-leg terms unless `use_yes_price: true`. |

Note the WS names `yes_dollars_fp` and `no_dollars_fp`. REST `GET /markets/{ticker}/orderbook` uses `orderbook_fp.yes_dollars` and `orderbook_fp.no_dollars`. Level order within the arrays is not specified for the WS snapshot. Kalshi's example is ascending; do not rely on it (**INFERRED**).

#### Delta example (AsyncAPI)

```json
{
  "type": "orderbook_delta",
  "sending_ts_ms": 1669149841123,
  "sid": 2,
  "seq": 3,
  "msg": {
    "market_ticker": "FED-23DEC-T3.00",
    "market_id": "9b0f6b43-5b68-4f9f-9f02-9a2d1b8ac1a1",
    "clock": 4182061,
    "price_dollars": "0.9600",
    "delta_fp": "-54.00",
    "side": "yes",
    "ts": "2022-11-22T20:44:01Z",
    "ts_ms": 1669149841000
  }
}
```

| Field | Type / unit | Notes |
|---|---|---|
| `msg.price_dollars` | string, dollars (4 dp) | price level |
| `msg.delta_fp` | string, signed contracts (2 dp) | "Fixed-point contract delta (2 decimals)" |
| `msg.side` | `yes` or `no` | |
| `msg.clock` | int64 ≥ 1 | see the rules below |
| `msg.ts_ms` | int64 ms | "Optional - Unix timestamp for when the orderbook change was recorded" |
| `msg.ts` | RFC3339 string | **deprecated**, use `ts_ms` |
| `msg.client_order_id` | string | "Optional - Present only when you caused this orderbook change." |
| `msg.subaccount` | int | Optional. Present only for your own orders when using subaccounts. |

Applying a delta is **INFERRED** because Kalshi does not spell it out: `level[side][price] += delta`, and delete the level when it reaches 0. Kalshi's two examples are not mutually consistent (a −54 delta at a yes level of 0.96 that is not in the snapshot), so do not use them as test vectors.

#### Pricing of the NO side (`use_yes_price`)

> By default, no-side deltas and snapshot levels are reported in **no-leg pricing**: a no-side delta at `price_dollars=0.30` corresponds to a market offer of "no at 30c", which would match against "yes at 70c". [getting_started/order_direction]

> **Migration plan.** The default for `use_yes_price` will be flipped to `true` in a future release, so subscriptions that don't explicitly set it will start receiving the unified yes-leg pricing automatically. The flag itself will then be removed in a subsequent release… [order_direction]

Recorder rule: always send `use_yes_price` explicitly and store it with the recording. With the default `false`, the best YES ask is `1 − max(no bid)`. That matches REST, e.g. "Best YES ask: $1.00 - (Highest price in the `no_dollars` array)".

#### Sequence numbers and `clock` (real-time mode, `update_interval_ms` 0 or omitted)

> - `clock` is the exchange clock. It is the same on every connection, so it can match a market's updates across redundant connections; `seq` counts messages on one subscription only
> - One exchange action can make several deltas, so several deltas can share a `clock`. Every connection sends them in the same order, before any delta for that market with a higher `clock`
> - A snapshot includes every change with a `clock` at or below its own; the deltas that follow it on that connection have higher clocks
> - While you are subscribed to a market, its clocks never go down outside exchange maintenance, but they skip values. They are not comparable across markets. Keep checking `seq` on each connection for missed messages
> - A market's clock may decrease during exchange maintenance, so don't compare clocks from before a maintenance period with clocks after it
> [websockets/orderbook-updates]

`seq` is per subscription (`sid`), covering all markets in that subscription. It is not per market. `clock` was added on 2026-10-29, so older recordings lack it.

#### What to do on a gap

> Apply every delta in `seq` order within its subscription. If you detect a gap, request `get_snapshot` for all subscribed markets, or `unsubscribe`, wait for `unsubscribed`, then `subscribe` again. A repeated `subscribe` alone does not resynchronize existing markets [orderbook-updates, conflated section; the same rule is in changelog 2026-11-05 and the Margin page]

> Snapshots bypass the interval and replace any unsent held changes for their market. Always replace your local book with a received snapshot before applying subsequent deltas for that market [orderbook-updates]

Implementation (**INFERRED** where the docs are silent):

1. Track `expected = last_seq + 1` per sid.
2. Count every message that carries this `sid` and a `seq`. `ok`, `unsubscribed`, `get_snapshot` replies and subscription-scoped `error` messages all carry `seq` in the schemas and examples. Whether they take a number in the same sequence is not stated, so treat any `seq` jump as a gap only after counting them.
3. On a gap, mark every market in that sid stale and send `get_snapshot` with all of them. The maximum number of tickers per `get_snapshot` is **UNCONFIRMED**, so chunk if there are many.
4. Replace each book when its snapshot arrives.

A REST snapshot (`GET /markets/{ticker}/orderbook`) has no `clock` or `seq`, so it cannot be spliced into the WS stream.

#### Conflated mode (`update_interval_ms: 100 | 1000`)

This is dated 2026-11-05 in the changelog, two days after this document; see Part 3. Key rules [orderbook-updates]:

> - Each window produces one `orderbook_delta` per changed price level, carrying the net held change at that level. Levels whose held changes cancel out are skipped. Apply every delta in sequence to account for those changes exactly
> - A conflated delta's `clock` describes that price level's latest included change, not the completeness of the whole book. Clocks can decrease between messages… Do not discard a delta because its clock is lower than a previously received clock
> - Between flushes, public levels can lag your own orders, and the book can appear locked or crossed. A flush contains separate delta messages, not an atomic full-book snapshot; there is no end-of-flush message
> - `seq` stays contiguous; the interval is fixed for the life of the subscription
> - A repeated `subscribe` must use the existing `update_interval_ms` (omitting it means `0`). A different valid interval returns error code 11 without adding markets.

**A recorder should use real-time mode (0).** Conflation loses intra-window book states, which LIP scoring needs (Part 2).

### 1.5.2 `ticker` (message type `ticker`)

> - No additional channel-level authentication beyond the authenticated WebSocket connection
> - Market specification optional (omit to receive all markets)
> - Supports `market_ticker`/`market_tickers` and `market_id`/`market_ids`
> - Updates sent whenever any ticker field changes [websockets/market-ticker]

Size-only changes also trigger updates (changelog 2026-02-12).

```json
{
  "type": "ticker",
  "sending_ts_ms": 1669149841123,
  "sid": 11,
  "msg": {
    "market_id": "9b0f6b43-5b68-4f9f-9f02-9a2d1b8ac1a1",
    "market_ticker": "FED-23DEC-T3.00",
    "price_dollars": "0.4800",
    "yes_bid_dollars": "0.4500",
    "yes_ask_dollars": "0.5300",
    "volume_fp": "33896.00",
    "open_interest_fp": "20422.00",
    "dollar_volume": 16948,
    "dollar_open_interest": 10211,
    "yes_bid_size_fp": "300.00",
    "yes_ask_size_fp": "150.00",
    "last_trade_size_fp": "25.00",
    "ts": 1669149841,
    "ts_ms": 1669149841000,
    "time": "2022-11-22T20:44:01Z"
  }
}
```

| Field | Unit | Schema description |
|---|---|---|
| `price_dollars` | $ string | "Last traded price in dollars" |
| `yes_bid_dollars`, `yes_ask_dollars` | $ string | best YES bid and ask |
| `volume_fp` | contracts (2 dp) | "Fixed-point total contracts traded" |
| `open_interest_fp` | contracts (2 dp) | |
| `dollar_volume` | integer, whole $ | "Signed whole-dollar cumulative traded notional" |
| `dollar_open_interest` | integer, whole $ | "Signed whole-dollar open-interest notional" |
| `yes_bid_size_fp`, `yes_ask_size_fp` | contracts | sizes at the best bid and ask |
| `last_trade_size_fp` | contracts | size of the last trade |
| `ts_ms` | ms | `ts` (seconds) and `time` (RFC3339) are **deprecated** |

**No `seq`.** The `tickerPayload` requires only `type`, `sid` and `msg`, so gaps cannot be detected on this channel. There are no NO-side price fields. The format of the `send_initial_snapshot` snapshot is not documented (**UNCONFIRMED**; probably an ordinary `ticker` message).

**`ticker_v2`:**

> The `ticker_v2` WebSocket channel has been removed. This was an undocumented experimental channel intended as a v2 iteration of the ticker channel but was rolled back due to user feedback. [changelog 2026-02-12]

### 1.5.3 `trade` (message type `trade`)

> - No additional channel-level authentication beyond the authenticated WebSocket connection
> - Market specification optional (omit to receive all trades)
> - Updates sent immediately after trade execution [websockets/public-trades]

```json
{
  "type": "trade",
  "sending_ts_ms": 1669149841123,
  "sid": 11,
  "seq": 2,
  "msg": {
    "trade_id": "d91bc706-ee49-470d-82d8-11418bda6fed",
    "market_ticker": "HIGHNY-22DEC23-B53.5",
    "yes_price_dollars": "0.3600",
    "no_price_dollars": "0.6400",
    "count_fp": "136.00",
    "taker_side": "no",
    "taker_outcome_side": "no",
    "taker_book_side": "ask",
    "is_block_trade": false,
    "ts": 1669149841,
    "ts_ms": 1669149841000
  }
}
```

| Field | Unit / meaning |
|---|---|
| `trade_id` | UUID |
| `yes_price_dollars`, `no_price_dollars` | $ strings |
| `count_fp` | contracts (2 dp, fractional possible) |
| `taker_outcome_side` | `yes` or `no`: "buy-yes and sell-no produce 'yes'; buy-no and sell-yes produce 'no'" |
| `taker_book_side` | `bid` or `ask`. "'bid' is equivalent to taker_outcome_side 'yes'". |
| `taker_side` | **deprecated** but still required in the schema |
| `is_block_trade` | "True if the trade was matched off book as a block trade" (added 2026-08-13) |
| `ts_ms` | ms. `ts` (seconds) is deprecated. |

Sequenced. The changelog of 2026-09-10 says "These channels have always been sequenced." The message has no `market_id`. There is no snapshot or recovery mechanism. **INFERRED:** backfill a gap from public REST `GET /markets/trades`.

### 1.5.4 `market_lifecycle_v2` (types `market_lifecycle_v2`, `event_lifecycle`, `event_fee_update`)

There is no `market_lifecycle` v1 channel in the current spec; the channel enum lists only `market_lifecycle_v2`.

> - No additional channel-level authentication beyond the authenticated WebSocket connection
> - Receives all market and event lifecycle notifications (`market_ticker` filters are not supported)
> - Event creation notifications [websockets/market-and-event-lifecycle]

KXMVE combo markets are excluded and go to `multivariate_market_lifecycle` (changelog 2026-02-12 and 2026-03-19).

`msg.event_type` takes these values: `created`, `activated`, `deactivated`, `close_date_updated`, `determined`, `settled`, `price_level_structure_updated`, and `metadata_updated` (which has its own schema).

| Field | Present when | Unit |
|---|---|---|
| `market_ticker` | always | |
| `exchange_index` | `created` | shard id |
| `open_ts` | `created` | seconds |
| `close_ts` | `created`, `close_date_updated` | seconds |
| `determination_ts`, `result`, `settlement_value` | `determined` | seconds; result string; `settlement_value` in fixed-point $ (e.g. "0.5000") |
| `settled_ts` | `settled` | seconds |
| `is_deactivated` | pause or unpause | bool, "only be interpreted for an open market" |
| `additional_metadata` | `created` | `name`, `title`, `yes_sub_title`, `no_sub_title` (deprecated), `rules_primary`, `rules_secondary`, `can_close_early`, `event_ticker`, `expected_expiration_ts`, optional `strike_type`, `floor_strike`, `cap_strike`, `custom_strike` |
| `price_level_structure`, `price_ranges` (`[{start,end,step}]` in $) | `created`, `price_level_structure_updated` | |
| `strike_type`, `floor_strike`, `cap_strike`, `custom_strike`, `yes_sub_title` | `metadata_updated` | strikes are JSON numbers |

Implicit transitions emit **no** event:

> `initialized` → `active`: when `open_time` passes. There is no `activated` WebSocket event for this transition. [getting_started/market_lifecycle]

`active`/`inactive` → `closed` at `close_time` is also implicit. Also:

> The market may not be queryable immediately after a `created` event. Retry with backoff. [market_lifecycle]

Examples (AsyncAPI):

```json
{"type": "market_lifecycle_v2", "sending_ts_ms": 1669149841234, "sid": 13, "seq": 3,
 "msg": {"market_ticker": "INXD-23SEP14-B4487", "exchange_index": 0, "open_ts": 1694635200, "close_ts": 1694721600,
         "additional_metadata": {"name": "S&P 500 daily return on Sep 14", "title": "S&P 500 closes up by 0.02% or more",
           "yes_sub_title": "S&P 500 closes up 0.02%+", "no_sub_title": "S&P 500 closes up <0.02%",
           "rules_primary": "The S&P 500 index level at 4:00 PM ET...", "rules_secondary": "", "can_close_early": true,
           "event_ticker": "INXD-23SEP14", "expected_expiration_ts": 1694721600, "strike_type": "greater", "floor_strike": 4487},
         "event_type": "created", "price_level_structure": "linear_cent"}}

{"type": "market_lifecycle_v2", "sending_ts_ms": 1669149841234, "sid": 13, "seq": 4,
 "msg": {"market_ticker": "INXD-23SEP14-B4487", "event_type": "price_level_structure_updated", "price_level_structure": "deci_cent",
         "price_ranges": [{"start": "0.0000", "end": "1.0000", "step": "0.0010"}]}}

{"type": "market_lifecycle_v2", "sending_ts_ms": 1669149841234, "sid": 13, "seq": 5,
 "msg": {"event_type": "metadata_updated", "market_ticker": "KXBTC-25APR30-T0915-B95000", "strike_type": "between", "floor_strike": 95000, "cap_strike": 95250}}

{"type": "event_lifecycle", "sending_ts_ms": 1669149841234, "sid": 5, "seq": 8,
 "msg": {"event_ticker": "KXQUICKSETTLE-26JAN25H2150", "exchange_index": 0, "title": "What will 1+1 equal on Jan 25 at 21:50?",
         "subtitle": "Jan 25 at 21:50", "collateral_return_type": "MECNET", "series_ticker": "KXQUICKSETTLE"}}

{"type": "event_fee_update", "sending_ts_ms": 1669149841234, "sid": 5, "seq": 9,
 "msg": {"event_ticker": "KXBTCD-26MAY2018", "fee_type_override": "quadratic", "fee_multiplier_override": 1}}
```

Constructed from the schema for illustration (not a Kalshi example), a determination looks like `{"type":"market_lifecycle_v2","sid":13,"seq":10,"msg":{"market_ticker":"…","event_type":"determined","determination_ts":…,"result":"yes","settlement_value":"1.0000"}}`.

Valid `price_level_structure` values: `linear_cent`, `deci_cent`, `tapered_deci_cent`, `center_{whole|half|quint|deci|centi}_edge_{…}_cent` variants, `banded_centi_cent`, and `""` (unknown).

> `price_ranges` … This is the source of truth for valid prices [getting_started/fixed_point_migration]

Live KXBTC15M markets currently use `tapered_deci_cent`: $0.001 ticks below $0.10 and above $0.90, $0.01 between (observed 2026-11-03).

### 1.5.5 CF Benchmarks: `cfbenchmarks_value` and `cfbenchmarks_value_5hz`

**`cfbenchmarks_value`** (about 1/s):

> Real-time CF Benchmarks index value updates, each carrying the raw upstream frame plus trailing 60-second and quarter-hour final-minute averages. Requires authentication.

> - Index specification via `index_ids` (array of CF Benchmarks index IDs, for example `["BRTI", "ETHUSD_RTI"]`)
> - `market_ticker`/`market_tickers`/`market_id`/`market_ids` are not supported for this channel
> - Use `index_ids: ["all"]` to receive every available index
> - Ticks are emitted roughly once per second; duplicate or out-of-order upstream source timestamps are ignored.
> - If you subscribe without any `index_ids`, no value events flow until you add indices or switch to `["all"]`
> - A successful `subscribe` response alone does not confirm that a requested index is available. [websockets/cfbenchmarks-value]

Index ids: AAVE `AAVEUSD_RTI`, ADA `ADAUSD_RTI`, BCH `BCHUSD_RTI`, BNB `BNBUSD_RTI`, **BTC `BRTI`**, DOGE `DOGEUSD_RTI`, DOT `DOTUSD_RTI`, **ETH `ETHUSD_RTI`**, HBAR `HBARUSD_RTI`, HYPE `HYPEUSD_RTI`, LINK `LINKUSD_RTI`, LTC `LTCUSD_RTI`, NEAR `NEARUSD_RTI`, SHIB/kSHIB `SHIBUSD_RTI` (USD per SHIB, unscaled), SOL `SOLUSD_RTI`, SUI `SUIUSD_RTI`, VVV `VVVUSD_RTI`, WLD `WLDUSD_RTI`, XLM `XLMUSD_RTI`, XRP `XRPUSD_RTI`, ZEC `ZECUSD_RTI`. Use `indexlist` to see what is actually streaming.

```json
{
  "type": "cfbenchmarks_value",
  "sending_ts_ms": 1669149841234,
  "sid": 1,
  "seq": 42,
  "msg": {
    "index_id": "BRTI",
    "received_at": 1710000000123,
    "data": "{\"type\":\"value\",\"id\":\"BRTI\",\"time\":1710000000123,\"value\":\"68000.12\"}",
    "avg_60s_data": {"value": "68000.12000000", "window_size": 3, "window_start_ts_ms": 1709999940123, "window_end_ts_exclusive": 1710000000123},
    "last_60s_windowed_average_15min": {"value": "68000.23000000", "window_size": 14, "window_start_ts_ms": 1709999980000, "window_end_ts_exclusive": 1710000000123}
  }
}
```

| Field | Unit / meaning |
|---|---|
| `index_id` | CF index id |
| `received_at` | ms. "When Kalshi received the upstream frame" |
| `data` | **string** holding the raw CF JSON frame (`type`, `id`, `time` in ms, `value` as a USD string). This channel has no top-level `value_usd`, so the tick value comes from `data` (**INFERRED**). |
| `avg_60s_data` | always present: `value` (USD, "formatted to 8 decimal places"), `window_size` (int ticks), `window_start_ts_ms`, `window_end_ts_exclusive` (ms) |
| `last_60s_windowed_average_15min` | optional, same shape |

Averaging semantics, verbatim:

> `avg_60s_data` (always present):
> - Window is trailing and per tick: `[source_ts_ms - 60000, source_ts_ms)`
> - `window_size` counts prior ticks only
> - If there are no prior ticks in the trailing window, the average falls back to the current tick value
>
> `last_60s_windowed_average_15min` (present only in the final minute before quarter-hour close: `:00`, `:15`, `:30`, `:45`):
> - Active accumulation window is `(quarter_close_ts_ms - 60000, quarter_close_ts_ms]`
> - The start-boundary tick is excluded and the close tick is included
> - This produces second-indexed counts: `:01 -> 1`, `:14 -> 14`, `:59 -> 59`, close tick (`:00/:15/:30/:45`) -> `60`
> - The field is omitted outside that final-minute window

This lines up with the 15-minute crypto settlement rule on KXBTC15M ("At the last minute before expiration, 60 RTI prices are collected. The official and final value is the average of these prices"). Kalshi does **not** say that the WS average equals the official settlement value (**UNCONFIRMED**). Treat it as an estimate and take the settlement from the lifecycle `determined` event (`settlement_value`) or from REST.

**`cfbenchmarks_value_5hz`** (added 2026-09-03):

> It carries BTC (`BRTI`), ETH (`ETHUSD_RTI`), SOL (`SOLUSD_RTI`), XRP (`XRPUSD_RTI`), and DOGE (`DOGEUSD_RTI`) at up to five updates per second. … Messages are lean raw ticks — they do not include the 60-second or quarter-hour averages, which stay on the per-second channel. [websockets/cfbenchmarks-value-5hz]

```json
{
  "type": "cfbenchmarks_value_5hz",
  "sending_ts_ms": 1669149841234,
  "sid": 1,
  "seq": 42,
  "msg": {
    "index_id": "BRTI",
    "value_usd": "68000.12000000",
    "source_ts_ms": 1710000000323,
    "received_at": 1710000000341,
    "data": "{\"type\":\"value\",\"id\":\"BRTI\",\"time\":1710000000323,\"value\":\"68000.12\"}"
  }
}
```

| Field | Unit |
|---|---|
| `value_usd` | "Index value in USD, formatted with exactly 8 decimal places" |
| `source_ts_ms` | "Upstream publication timestamp of the tick (unix ms)" |
| `received_at` | ms |
| `data` | raw CF frame as a string |

Index-list reply (both channels; the 5Hz one is typed `cfbenchmarks_value_5hz_indexlist` and lists ids "recently observed on the 5Hz stream"):

```json
{"type": "cfbenchmarks_value_indexlist", "sending_ts_ms": 1669149841234, "id": 2, "sid": 1, "seq": 1, "msg": {"index_ids": ["BRTI", "ETHUSD_RTI"]}}
```

Both CF channels are sequenced. The pages give no recovery procedure. Historical ticks are available via the REST passthrough `GET /trade-api/v2/cfbenchmarks/history/values?id=BRTI&timespan=HOUR&timestamp=…`. It needs authentication, "is available only to accounts with the appropriate entitlement", and costs 50 tokens per request.

Whether the CF **WebSocket** channels need an entitlement beyond authentication is **UNCONFIRMED**. The pages only say "Requires authentication". Error 9 covers "channel access that was not granted". (`pyth_value` is paid: "$1,000/month, with the first seven days free".)

### 1.5.6 Other channels (not needed for market data)

`fill`, `user_orders`, `market_positions`, `order_group_updates` and `communications` are private and user-specific. `multivariate_market_lifecycle` carries combo markets. `pyth_value` carries Pyth prices and Treasury yields, which are paid.

## 1.6 Units cheat sheet

| Pattern | Representation | Example |
|---|---|---|
| `*_dollars`, `price_dollars`, `settlement_value`, `price_ranges[*].start/end/step` | fixed-point **dollar** string, "up to 4 decimal places" (WS always shows 4) | `"0.4800"` = 48¢ |
| `*_fp` contract fields (`count_fp`, `delta_fp`, `volume_fp`, `*_size_fp`, `target_size_fp`) | fixed-point **contracts**, 2 dp, fractional allowed. "For integer arithmetic, represent quantities in hundredths of a contract: `"1.55"` is 155 units." | `"136.00"` |
| `yes_dollars_fp` / `no_dollars_fp` (WS snapshot) | array of `[dollar_price, contract_count]` strings | `[["0.0800","300.00"]]` |
| `dollar_volume`, `dollar_open_interest` (ticker) | signed integer, whole dollars | `16948` |
| `ts_ms`, `sending_ts_ms`, `received_at`, `source_ts_ms`, `window_*_ts*` | integer Unix **ms** | |
| `ts` (ticker/trade), `open_ts`, `close_ts`, `determination_ts`, `settled_ts` | integer Unix **seconds** (ticker/trade `ts` deprecated) | |
| CF `value`, `value_usd` | USD string, 8 dp | `"68000.12000000"` |
| Incentive `period_reward`, `max_reward_per_account` | integer **centi-cents** (1 = $0.0001) | `1150000` = $115.00 |
| Incentive `discount_factor_bps` | integer basis points (10000 = 1.0) | `5000` = 0.5 |
| Series `fee_multiplier` | JSON number (double) | `1` |

> Use each field's documented unit and precision: the `_fp` suffix alone does not distinguish contract quantities from dollar amounts. [fixed_point_migration]

Legacy integer-cent price fields and integer count fields were **removed** from REST and WebSocket payloads on 2026-03-12 (announced 2026-03-08), and the last stragglers went on 2026-04-02. Recorders and parsers should expect only `_dollars` and `_fp` fields.

## 1.7 Limits, keep-alive and rate limits

### Keep-alive

> Kalshi sends Ping frames (`0x9`) every 10 seconds with body `heartbeat` to maintain the connection. Clients should respond with Pong frames (`0xA`). Clients may also send Ping frames to which Kalshi will respond with Pong. [websockets/connection-keep-alive]

> The Python `websockets` library automatically handles WebSocket ping/pong frames to keep connections alive. [quick_start_websockets]

The server's timeout for an unanswered ping is **UNCONFIRMED**. As a heuristic, treat 30 s or more without any frame as a dead connection and reconnect (**INFERRED**).

### Connections and subscriptions

> Predictions and Perps (Margin) WebSocket connections share a **per-user limit on concurrent open connections**. [rate_limits]

| Tier | Max concurrent WS connections |
|---|---|
| Basic, Advanced, Expert | 200 |
| Premier | 500 |
| Paragon | 750 |
| Prime, Prestige | 1,000 |

> When you reach the connection limit, new WebSocket handshakes return `429 Too Many Requests`. [rate_limits]

The limit is per **user**, not per key, so the recorder and the paper desk share it if they use the same account.

Other limits:

- "Sanity limits enforced on orderbook subscriptions: Max 500k market subscriptions per session. Max 10k/s commands per second enforced." (changelog 2026-06-18)
- Error 26 is "Adding markets would exceed the per-subscription market limit". The number is **UNCONFIRMED** beyond the 500k/session figure.
- Error 27 is "The subscription exceeded its command rate limit". The number is **UNCONFIRMED**.
- One `orderbook_delta` subscription per connection.
- Message size: "the 64 MiB message limit" (changelog 2026-09-24).
- Compression: "Public WebSocket connections support RFC 7692 `permessage-deflate` compression when the client offers it during the opening handshake." The Python `websockets` library offers it by default; that is library behaviour, not something Kalshi documents.
- Message rates: CF about 1/s per index; 5Hz up to 5/s per index; ticker "whenever any ticker field changes". No server-side rate cap on market data is documented. Error 25 (buffer overflow) is the failure mode for slow readers.

Whether WS commands or connections draw REST tokens is not documented (**UNCONFIRMED**). They appear to be limited separately, by the limits above.

### Maintenance

> Every **Thursday from 3:00 AM to 5:00 AM ET**, Kalshi runs scheduled maintenance. … Clients should be prepared for session disconnections during this window and reconnect after 5:00 AM ET. [getting_started/maintenance_and_pauses]

Orderbook clocks may decrease across maintenance (see 1.5.1).

### REST rate limits (token buckets)

> Every authenticated request costs **tokens**. Your tier sets your **budget**: the rate, in tokens per second, at which your balance refills. Your sustained rate for an endpoint is `budget ÷ cost`.
> Most requests cost the default of **10 tokens**. [getting_started/rate_limits]

Read and Write are separate buckets ("The split is by operation type, not by protocol").

| Tier | Read tokens/s | Write tokens/s | Read req/s at cost 10 | Write req/s at cost 10 | Read bucket capacity | Write bucket capacity |
|---|---|---|---|---|---|---|
| Basic | 200 | 100 | 20 | 10 | 3 s (600) | 1 s (100) |
| Advanced | 300 | 300 | 30 | 30 | 3 s (900) | 3 s (900) |
| Expert | 600 | 600 | 60 | 60 | 1 s (600) | 3 s (1,800) |
| Premier | 1,200 | 1,200 | 120 | 120 | 1 s | 3 s (3,600) |
| Paragon | 2,400 | 2,400 | 240 | 240 | 1 s | 3 s |
| Prime | 4,800 | 4,800 | 480 | 480 | 1 s | 3 s |
| Prestige | 12,000 | 9,600 | 1,200 | 960 | 1 s | 3 s |

Capacity rule, verbatim:

> Basic and Advanced Predictions Read buckets, and Write buckets above the Basic tier, hold up to **three seconds of budget**. … Predictions Read buckets above Advanced, Perps Read buckets, and Basic-tier Write buckets hold one second of budget.

Tier qualification:

- Basic comes with signup.
- Advanced: call `POST /account/api_usage_level/upgrade`. "Criteria: at least 1 of the user's last 100 Predictions orders was created via API."
- Expert through Prestige are earned from trailing 30-day volume share, reviewed daily and granted for 30 days. Earn/Keep thresholds: Expert 0.075%/0.05%, Premier 0.125%/0.10%, Paragon 0.25%/0.20%, Prime 0.50%/0.40%, Prestige 1.00%/0.80%. They can also be assigned by Kalshi.

On a 429:

> A rate-limited request returns `429 Too Many Requests` with the body:
> `{"error": "too many requests"}`
> 429 responses do not currently include `Retry-After` or `X-RateLimit-*` headers. There is no penalty or cooldown. … Apply exponential backoff on 429. [rate_limits]

Other costs:

- `GET /portfolio/balance` has its own bucket: 1/s at Basic and Advanced, 5/s above.
- Live `GET /account/endpoint_costs`, which is public, returned `default_cost: 10` on 2026-11-03. Only non-default routes are listed. The relevant non-default ones are `GET /trade-api/v2/cfbenchmarks*` at 50 and `GET /portfolio/orders/:order_id` at 2. Market-data GETs cost 10.
- Rate limits for **unauthenticated** public REST GETs are **not documented** (**UNCONFIRMED**; probably IP-based). This matters here because the desk shares the IP.
- The token buckets belong to the user (**INFERRED** from "Your tier"), so authenticated REST calls from the recorder would draw on the desk's Read budget.

## 1.8 Relevant changes 2025–2026 (from the changelog)

| Date | Change |
|---|---|
| 2025-08-08 | `client_order_id` on `orderbook_delta` when your order caused the change |
| 2025-09-09 | "Any message bearing price in cents will now also bear an equivalent fixed-point dollars field" (subpenny) |
| 2025-09-10 | `GET /incentive_programs` announced ("not yet live") |
| 2025-09-18 | WS connections per user limited by tier, starting at 200 |
| 2025-09-21 / 10-01 | `GET /series/fee_changes` added; it returns user-facing fee type names |
| 2025-09-25 | Repeated subscribes no longer error; `list_subscriptions` command added |
| 2025-10-10 | `price_level_structure` moved from event to market level |
| 2025-10-13 | Incentive programs "now return a `series_ticker` field". **Absent today**; see Part 3. |
| 2026-01-06 | Cent price fields removed from Market responses (release 2026-01-15). `tick_size` replaced by `price_level_structure` and `price_ranges`. |
| 2026-01-22 | `*_fp` count fields documented in the AsyncAPI for orderbook, ticker and trades |
| 2026-02-05 | Incentive programs return `market_id` |
| 2026-02-11 | `skip_ticker_ack`; high-precision ticker `time` |
| 2026-02-12 | **`ticker_v2` removed.** `ticker` gains `yes_bid_size_fp`, `yes_ask_size_fp` and `last_trade_size_fp`, and size changes trigger updates. `market_lifecycle_v2` stops emitting KXMVE markets. |
| 2026-02-19 | `settlement_value` on `determined` lifecycle events (release 2026-02-26). Live/historical data split (`GET /historical/*`). |
| 2026-03-08 → 03-12 | **Legacy integer cents and integer count fields removed from all REST and WS payloads** (some restored on 03-11, all gone by 04-02) |
| 2026-03-12 | Lifecycle `price_level_structure_updated` event (and `fractional_trading_updated`, removed again 04-17) |
| 2026-03-19 | `multivariate_market_lifecycle` channel |
| 2026-03-30 | `GET /markets/orderbooks?tickers=` (up to 100) |
| 2026-04-15 | `ts_ms` added to ticker, trade and orderbook_delta; `ts` and `time` deprecated |
| 2026-04-20 | `get_snapshot` action on `orderbook_delta` |
| 2026-04-22/23 | Token-cost rate limits with separate Read and Write buckets; Paragon tier; write bursts; `GET /account/endpoint_costs` |
| 2026-05-05 / 05-11 / 06-18 | Lifecycle `metadata_updated` (floor_strike, then yes_sub_title, then strike_type, cap_strike and custom_strike) |
| 2026-05-06 | `taker_outcome_side` / `taker_book_side` on trades; `taker_side` deprecated |
| 2026-05-07 | Dedicated hosts `external-api.kalshi.com` and `external-api-ws.kalshi.com` |
| 2026-05-12 | Error 25 "Subscription buffer overflow" |
| 2026-06-05/11 | Volume-earned tiers and the `grants` array in `GET /account/limits` |
| 2026-06-18 | Sanity limits: 500k market subscriptions per session, 10k commands/s |
| 2026-07-02 | `price_ranges` on lifecycle `created` and `price_level_structure_updated` |
| 2026-07-22 | `GET /incentive_programs` excludes programs on hidden events |
| 2026-07-23 | Seven new price-level structures; `pyth_value`; subaccount-restricted keys can open WS |
| 2026-07-30 | `exchange_index` on lifecycle `created` and on `event_lifecycle` |
| 2026-08-06 | `multivariate` channel removed |
| 2026-08-13 | `is_block_trade` on trades |
| 2026-08-27 / 09-10 | Incentive `type=margin_maker_volume` / `margin_taker_volume` with `max_reward_per_account` |
| 2026-09-03 | `cfbenchmarks_value_5hz` channel |
| 2026-09-10 | AsyncAPI corrections: `seq` documented on trade, lifecycle and event messages ("have always been sequenced") |
| 2026-09-17 | Fix for events skipped right after `subscribed` |
| 2026-09-24 | Ed25519 keys; `permessage-deflate`; 64 MiB message limit; +20% Read/Write budgets for Premier and above |
| 2026-10-01 | `sending_ts_ms` on WS messages; `liquidity_dollars` removed from markets |
| 2026-10-15 | Balance endpoint gets its own bucket |
| 2026-10-29 | **`clock` on `orderbook_snapshot` and `orderbook_delta`**; warp-ws hosts for fill and user_orders |
| 2026-11-05 (future-dated) | **`update_interval_ms` conflation**; "Each connection has one `orderbook_delta` subscription"; `no_sub_title` deprecated |

The changelog has an RSS feed at `https://docs.kalshi.com/changelog/rss.xml`.

## 1.9 Recorder checklist (derived; INFERRED unless quoted above)

1. Connect to `wss://external-api-ws.kalshi.com/trade-api/ws/v2` with freshly signed headers. Answer pings. Reconnect with exponential backoff. Expect drops on Thursdays 03:00–05:00 ET.
2. Subscribe in separate commands:
   - `market_lifecycle_v2` with no filter;
   - `cfbenchmarks_value` and/or `cfbenchmarks_value_5hz` with explicit `index_ids`;
   - `orderbook_delta` with `market_tickers`, explicit `use_yes_price`, and no `update_interval_ms`;
   - `ticker` and `trade` with `market_tickers`.
   Use `skip_ticker_ack: true` when subscribing to many markets.
3. Store every raw frame with local receive time (wall and monotonic), connection id and `sending_ts_ms`. Rebuild books from the raw log, so a parser bug never loses data.
4. Keep `sid → channel` from `subscribed`. Check `seq` per sid on every sequenced channel. On an `orderbook_delta` gap, send `get_snapshot` for all markets in that sid. On other channels, log the gap and backfill from REST if needed.
5. Track new markets from `created` events and add them with `add_markets`. Markets open at `open_time` without an `activated` event.
6. Errors 10 and 25 are terminal: resubscribe. Ignore unknown `type` values and fields.
7. Parse all prices and sizes as `Decimal`. Never key logic off `price_level_structure` names; use `price_ranges`.

---

# Part 2. Liquidity Incentive Program and incentive-programs API

## 2.1 Program rules (help.kalshi.com article 13823851, fetched 2026-11-03)

> The Liquidity Incentive Program rewards you for placing resting orders that improve market liquidity. This program pays you for maintaining orders on the books that help other traders get better prices, even if your orders don't get filled.

**Dates:**

> **Program end:** January 1, 2027 … Kalshi can end or modify the program at any time.

The governing terms are at kalshi.com/regulatory/notices. I did not fetch them because the host is outside the allowed set.

**Eligibility, verbatim:**

> **Who can participate:** Most regular U.S. Kalshi members
>
> **Who cannot participate:**
> - Kalshi affiliates and employees
> - Introducing Brokers, FCMs, and their customers
> - International, non-U.S. users (ineligible for rewards)

**Market Maker Agreement holders:** the LIP article does **not** list them as excluded. The separate "Liquidity Provider Program" article (15410219) says "Members who have executed a Market Maker Agreement with Kalshi may become a Designated Liquidity Provider for the Incentivized Series". That program is paid through auctions and lists, for example, "Crypto 15min markets … Provider Count 2". Whether MMA holders or DLPs are also excluded from LIP is **UNCONFIRMED**; the regulatory notice terms would settle it.

**Snapshots:**

> Kalshi takes a snapshot of the order book once per second, at a random moment within each second

**Parameters, set per time period:**

> - **Target Size:** more than 100 and fewer than 20,000 contracts (the depth that must be resting on each side for a snapshot to count)
> - **Discount Factor:** up to 1.00 (sets how steeply orders priced below the Reference Price are discounted. At 1.00 there is no distance penalty at all, and the penalty steepens as the factor falls toward zero)

**Scoring, verbatim:**

> Step 1: Snapshot Scoring
> - Kalshi first finds the **Reference Price** for that snapshot. Walking down from the best bid, it is the first price level at which cumulative resting size reaches one fifth of the Target Size. It is calculated fresh for every snapshot rather than set in advance, and it is not always the best bid or ask - a small order alone at the top of the book does not set it
> - For each snapshot, Kalshi scores every resting order that helps reach the Target Size on its side
> - Each qualifying order is scored on order size (larger = higher score) and distance from the Reference Price (closer = higher score, using the Discount Factor)
> - If a side of the book never reaches the Target Size, no orders on that side qualify for that snapshot
>
> Step 2: Distance Penalty
> - Orders priced at or better than the Reference Price get full credit (1.0x multiplier)
> - Orders priced below the Reference Price get reduced credit: the Discount Factor raised to the number of ticks away
>
> Step 3: Size Weighting
> - Your raw score for an order = Order Size × Distance Multiplier
> - Raw scores are then normalized: each order is divided by the total raw score of all qualifying orders on that side. What counts is your *share* of qualifying liquidity, not your absolute size
> - Both sides count separately. Your snapshot score is your share of the yes side plus your share of the no side, so a single snapshot is worth at most 2.0 across all participants
>
> Step 4: Total Score and Payout
> - Your Time Period score = your total snapshot scores ÷ all participants' total snapshot scores
> - Your reward = Your Time Period Score × Time Period Reward × (non-excluded snapshots ÷ total snapshots), rounded down to the nearest cent

**Excluded snapshots, verbatim:**

> A snapshot is excluded from scoring if any of the following applies at the moment it is taken:
> - The market is not open for trading
> - There is not two-sided liquidity - resting orders must meet the Target Size on *both* the yes side and the no side
>
> Excluded snapshots reduce the amount paid out. The reward for a Time Period is scaled by the share of snapshots that were not excluded…
>
> **Example:** A Time Period has a $100 reward and 10,000 snapshots. 8,000 of them have two-sided liquidity meeting the Target Size, and 2,000 are excluded. If your share of the Time Period score is 20%, you would earn 20% × $100 × (8,000 ÷ 10,000) = $16.00.

**Sizes and caps:**

> - **Time periods:** Up to 31 days each, and time periods may overlap
> - **Daily rewards:** $1-$1,000 per market, per day
> - **Minimum payout:** $1.00 (rounded down to nearest cent)

No per-account cap is stated for LIP. The API has an optional `max_reward_per_account`, documented for the margin volume program types.

**Payout timing** (article 16076644):

> Rewards are not credited in real time. Final scoring occurs **after a program ends**, and payment follows in a later processing run. Timing can vary.

> For liquidity programs, rewards are rounded down to the nearest cent, and a final reward below $1 for an individual program is not paid.

Paid rewards appear as credits under Rewards and under Account → Activity → Credits. A verified SSN is required above IRS reporting thresholds.

**Answers to the specific questions:**

- **Distance from what?** From the per-snapshot **Reference Price**: the first level, walking down from the best bid, where cumulative size reaches Target/5. It is not measured from the best price.
- **Halving per tick?** Only when the Discount Factor is 0.5. All five active programs sampled on 2026-11-03 had `discount_factor_bps: 5000`, which is a 0.5 multiplier per tick below the Reference Price. The factor is set per program ("up to 1.00").
- **Minimum order size?** None is stated. Target Size (100 to 20,000 contracts) is a **side-depth** requirement, not a per-order minimum.
- **Both sides?** Yes. Each side is scored separately (shares sum to 1 per side), and both sides must reach Target Size or the snapshot is excluded.

## 2.2 Reward formula in closed form (derived)

Notation: `N` is the total number of snapshots in the period (≈ the period length in seconds, **INFERRED** from "once per second"). `P` is the period reward. `share_{u,s,side}` is user `u`'s normalized share on a side in snapshot `s`, and 0 in excluded snapshots.

In every non-excluded snapshot both sides reached Target Size, so all participants' snapshot scores sum to exactly 2.0. Substituting into Step 4 gives:

```
reward_u = floor_to_cent( P × Σ_s (share_{u,s,yes} + share_{u,s,no}) / (2 × N) )     and paid only if ≥ $1.00
```

In words, each snapshot has a pool of `P/(2N)` per side, split by qualifying-liquidity share. For the live example below this is `$115 / (2 × 381,535)` ≈ $0.000151 per side per second. This algebra is mine (**INFERRED**), but it follows from the article's Step 4 and its exclusion rule.

Per-snapshot, per-side scoring sketch (**INFERRED** where the article is silent):

```python
def side_shares(levels, my_size_at, target, df, ticks_below):
    """levels: [(price, total_size)] for ONE side (that side's own bid prices), best (highest) first.
    my_size_at: price -> my resting size at that price. Returns my share on this side, or None if the side
    fails Target Size (then the whole snapshot is excluded)."""
    if sum(s for _, s in levels) < target:
        return None
    cum, ref = 0, None
    for p, s in levels:                      # Reference Price: first level where cumulative size >= target/5
        cum += s
        if cum >= target / 5:
            ref = p
            break
    cum, total_raw, my_raw = 0, 0, 0
    for p, s in levels:                      # orders that "help reach the Target Size"
        if cum >= target:
            break
        mult = 1.0 if p >= ref else df ** ticks_below(ref, p)
        total_raw += s * mult                # UNCONFIRMED: whole level, or only the part up to the target?
        my_raw += my_size_at.get(p, 0) * mult  # UNCONFIRMED: time priority inside the marginal level
        cum += s
    return my_raw / total_raw
```

What a recorder must capture to estimate LIP from its own data:

- the full-depth book on both sides at 1 s resolution or finer (real-time `orderbook_delta`, not conflated);
- the market's open or paused state from lifecycle events and REST status;
- the program parameters from `GET /incentive_programs`;
- your own resting orders, for the numerator only (needs authenticated private channels).

Kalshi's own snapshot instants are random within each second and cannot be reproduced exactly.

## 2.3 REST: `GET /incentive_programs`

Path: `GET https://api.elections.kalshi.com/trade-api/v2/incentive_programs` (operationId `GetIncentivePrograms`). It is **public**: there is no `security` block in the OpenAPI, and my unauthenticated calls returned 200.

| Query param | Values | Default |
|---|---|---|
| `status` | `all`, `active`, `upcoming`, `closed`, `paid_out` | `all` |
| `type` | `all`, `liquidity`, `volume`, `margin_maker_volume`, `margin_taker_volume` | `all` |
| `incentive_description` | "Filter by exact incentive description." | none |
| `limit` | 1–10000. "Defaults to 100. Maximum value is 10000." | 100 |
| `cursor` | from the previous `next_cursor` | none |

There is **no market_ticker or series filter** in the current spec, although the 2025-09-10 changelog spoke of "filtering … by market ticker". To find a market's programs, page through the list and filter client-side.

Response: `{"incentive_programs": [IncentiveProgram], "next_cursor": "<string>"}`. `next_cursor` was `""` when there were no more pages.

| Field | Type | OpenAPI description / unit |
|---|---|---|
| `id` | string | "Unique identifier for the incentive program" |
| `market_id` | string (UUID) | market UUID (added 2026-02-05) |
| `market_ticker` | string | |
| `incentive_type` | enum | `liquidity`, `volume`, `margin_maker_volume`, `margin_taker_volume` |
| `incentive_description` | string | "Plain text description". Live value: `"new_event"`. |
| `start_date`, `end_date` | RFC3339 date-time | the Time Period |
| `period_reward` | int64 | "Total reward for the period in **centi-cents**" (÷10,000 gives USD). This is the "Time Period Reward" in 2.1 (**INFERRED** mapping). |
| `paid_out` | bool | "Whether the incentive has been paid out" |
| `discount_factor_bps` | int32, nullable | "Discount factor in basis points (optional)". ÷10,000 gives the Discount Factor. |
| `target_size_fp` | FixedPointCount string, nullable | "target size for the incentive program (optional)" in contracts |
| `max_reward_per_account` | int64, nullable | "Maximum reward per account in centi-cents (optional)". Changelog: on margin volume types. |

**Live example** (first element of `GET /incentive_programs?status=active&limit=5`, 2026-11-03 20:26 UTC, verbatim):

```json
{
    "incentive_programs": [
        {
            "discount_factor_bps": 5000,
            "end_date": "2026-11-08T05:00:00Z",
            "id": "ffed1b99-53e9-4bc8-874c-30407cbc441a",
            "incentive_description": "new_event",
            "incentive_type": "liquidity",
            "market_id": "01a19d1b-9c66-7cc4-96d6-cd97a2a8bad7",
            "market_ticker": "KXIBONDFIX-27MAY03-T1.6",
            "paid_out": false,
            "period_reward": 1150000,
            "start_date": "2026-11-03T19:01:05Z",
            "target_size_fp": "1000.00"
        }
    ],
    "next_cursor": "CgYI8d6o1wYSJGFhYTIwZTE3LTZiZmMtNDBjYS1iNGQ3LTI3M2Q2NmQ4ZTQzMQ"
}
```

Reading it:

- The pool is $115.00 over 381,535 s (4.416 days), about $26.04/day. That is inside the article's "$1-$1,000 per market, per day".
- Discount Factor is 0.50. Target Size is 1,000 contracts, so the Reference Price is set at 200 contracts of cumulative depth.
- The other four results were the same shape: KXIBONDFIX-27MAY03-T1.0 with 1,150,000; KXLAMEDUCKCONF-27JAN03-AL25, -AL50 and -AL75 with 1,350,000. All had 5000 bps and "1000.00".
- `series_ticker` is **not** present.
- `GET /incentive_programs?status=active&type=volume&limit=2` returned `{"incentive_programs": [], "next_cursor": ""}`.

## 2.4 Fees: series fields, `fee_changes` and event overrides

### Series fields (`GET /series/{series_ticker}` and `GET /series`; public)

| Field | Type | OpenAPI description |
|---|---|---|
| `fee_type` | enum `quadratic`, `quadratic_with_maker_fees`, `quadratic_with_combo_maker_fees`, `flat` | "FeeType is a string representing the series' fee structure. Fee structures can be found at https://kalshi.com/docs/kalshi-fee-schedule.pdf. 'quadratic' is described by the General Trading Fees Table, 'quadratic_with_maker_fees' is described by the General Trading Fees Table with maker fees described in the Maker Fees section, 'quadratic_with_combo_maker_fees' is the same maker-fee structure with a 0.5 maker multiplier instead of 0.25, 'flat' is described by the Specific Trading Fees Table." |
| `fee_multiplier` | number (double) | "FeeMultiplier is a floating point multiplier applied to the fee calculations." |

Live `GET /series/KXBTC15M` (2026-11-03, fee-relevant fields verbatim): `"fee_multiplier": 1`, `"fee_type": "quadratic"`, `"exchange_index": 2`, `"frequency": "fifteen_min"`, `"ticker": "KXBTC15M"`.

The fee formula itself is not on docs.kalshi.com or help.kalshi.com. The Fees help article only links the PDF. The commonly cited model, taker fee ≈ `fee_multiplier × 0.07 × C × P × (1 − P)` with maker fees at 0.25× the taker coefficient for `quadratic_with_maker_fees`, is **UNCONFIRMED** here. The 0.25 maker ratio does match the OpenAPI wording above. For rounding, the Fee Rounding page says the trade fee is the "Fee from the fee model, rounded up to the nearest `$0.000001`", plus a separate rounding fee and rebate that restore balance precision ($0.0001 for direct members, $0.01 for non-direct).

### `GET /series/fee_changes` (public)

| Param | Type | Notes |
|---|---|---|
| `series_ticker` | string, optional | omit for all series |
| `show_historical` | bool, default false | From the changelog (2025-09-21): "If … set to true, ALL fee changes previous and upcoming will be shown. If set to false, only upcoming fee changes will be shown" |

Response: `{"series_fee_change_arr": [{"id", "series_ticker", "fee_type", "fee_multiplier", "scheduled_ts"}]}`. `scheduled_ts` is "Timestamp when this fee change is scheduled to take effect" (date-time). The endpoint is not paginated.

Live results, 2026-11-03:

- `?series_ticker=KXBTC15M&show_historical=true` returned `{"series_fee_change_arr": []}`.
- With no params (upcoming, all series) it returned `[]`.
- `?show_historical=true` returned 107 entries from 2025-10-04T07:00:00Z to 2026-09-03T18:35:23Z. Fee types: 64 `quadratic_with_maker_fees`, 39 `quadratic`, 4 `quadratic_with_combo_maker_fees`. Multipliers: 1 (74), 0.5 (19), 0 (14).

Sample entries, verbatim:

```json
{"fee_multiplier": 1, "fee_type": "quadratic_with_maker_fees", "id": "ab7eeb97-1196-421c-b79a-b05e96832628", "scheduled_ts": "2026-09-03T18:35:23Z", "series_ticker": "KXA100MS"}
{"fee_multiplier": 0, "fee_type": "quadratic", "id": "80e167b5-0272-438c-b68f-4cd2c9f470b3", "scheduled_ts": "2026-02-26T03:15:00Z", "series_ticker": "KXBTCY"}
```

### Event-level overrides

`GET /events/fee_changes?event_ticker=&limit=&cursor=` returns `{"event_fee_changes": [{"id", "event_ticker", "series_ticker", "fee_type_override", "fee_multiplier_override", "scheduled_ts"}], "cursor"}`. I did not fetch it live.

> Event fees are an override layered on top of the parent series' fee structure. If `fee_type_override` and `fee_multiplier_override` are null, that indicates the override is cleared. [api-reference/events/get-event-fee-changes]

The same overrides stream on `market_lifecycle_v2` as `event_fee_update` (section 1.5.4). Its enum also allows `margin_market_maker_program_fees`.

---

# Part 3. Unclear, contradictory or unconfirmed

1. **Future-dated changes.** The changelog dates `update_interval_ms` conflation, "Each connection has one `orderbook_delta` subscription" and the `no_sub_title` deprecation **2026-11-05**, two days after this document. The reference pages already describe them as current, and the Fixed-Point page says "Last Updated: November 5, 2026". They may not be live yet. Do not depend on conflation.
2. **Sequencing of control messages.** `ok`, `unsubscribed`, `*_indexlist` and subscription-scoped `error` messages carry `seq` in the schemas and examples. The docs do not say whether they take a number in the data sequence. Gap detection must account for them; verify empirically.
3. **Which channels need auth.** The Quick Start still lists the `multivariate` channel as public, but it was removed on 2026-08-06. `orderbook_delta` is labelled "Private" and "Authentication required" even though it carries the public book. This is moot in practice because every connection must be authenticated (confirmed: 401 without a key).
4. **Lifecycle filters.** The AsyncAPI example `subscribeAllChannelsOneMarket` puts `market_lifecycle_v2` together with a `market_ticker`, while the channel says "`market_ticker` filters are not supported". It is unclear whether the filter is ignored or rejected. Subscribe to lifecycle on its own.
5. **REST orderbook order.** The endpoint description says levels are "organized from best to worst prices" and include "order counts". The Orderbook Responses page and the live response (`depth=4`, 2026-11-03) show ascending prices with the best bid **last** and only `[price, count]` pairs.
6. **`no_sub_title`.** Kalshi says it "has equaled `yes_sub_title` on every market created since September 2024". The live KXBTC15M market had `no_sub_title: "Target price: TBD"` against `yes_sub_title: "Target Price: $77,547.59"`.
7. **Incentive programs.** `series_ticker` was announced on 2025-10-13 but is absent from the OpenAPI schema and from live responses. The market-ticker filter mentioned on 2025-09-10 does not exist in the current spec.
8. **Example values.** The CF `last_60s_windowed_average_15min` example (start 15:59:40Z, `window_size` 14, end after the :00 close) contradicts the documented semantics. The orderbook snapshot and delta examples are not mutually consistent. Use the prose rules.
9. **Stale rate-limit example.** The 2026-04-30 changelog example (`"usage_tier": "advanced"`, read 200, write 100) does not match the current table (Advanced 300/300).
10. **`taker_side` removal date.** It is "not … removed before May 14, 2026" in the AsyncAPI and "May 28, 2026" on the Order direction page. It is still required in the schema.
11. **Web key default.** The API Keys page says "Ed25519 is selected by default" in the web UI. The 2026-09-24 changelog says "web-generated keys remain RSA for now". Detect the type from the parsed key. The repo's `kalshi/auth.py` is RSA-only.
12. **Undocumented values:** the per-subscription market limit (error 26) apart from 500k/session; the per-subscription command rate (error 27); the maximum tickers per `get_snapshot`; the server's pong timeout; timestamp skew tolerance for signatures; unauthenticated REST rate limits (relevant to the shared IP); whether WS usage draws REST tokens; whether the CF WS channels need an entitlement; the format of the ticker `send_initial_snapshot`; the contents of the "External Feeds" socket.
13. **LIP ambiguities:**
    - whether the order that crosses the Target Size counts in full or in part;
    - how orders within the marginal level are ranked;
    - how "ticks away" is counted when a tapered price grid changes step between bands (KXBTC15M is `tapered_deci_cent`);
    - whether Market Maker Agreement holders or Designated Liquidity Providers are excluded (the LIP article does not say);
    - exact payout timing ("Timing can vary");
    - the web "blue dot" estimate is "based on distance from the top of the book", while scoring uses the Reference Price.
14. **Fee formula coefficients** are not in the allowed sources (they are in kalshi.com/docs/kalshi-fee-schedule.pdf, not fetched).

---

## Appendix A. Requests made (2026-11-03 UTC, all GET, no credentials, spaced at least 6 s apart, no 429s)

| Time | Status | URL |
|---|---|---|
| 20:21:20 | 200 | https://docs.kalshi.com/llms.txt |
| 20:21:43 | 200 | https://docs.kalshi.com/llms-full.txt |
| 20:22:59 | 200 | https://docs.kalshi.com/asyncapi.yaml |
| 20:24:06 | 200 | https://docs.kalshi.com/openapi.yaml |
| 20:24:46 | 200 | https://help.kalshi.com/llms.txt |
| 20:25:00 | 200 | https://help.kalshi.com/en/articles/13823851-liquidity-incentive-program.md |
| 20:25:13 | 200 | https://help.kalshi.com/en/articles/16076644-liquidity-incentive-programs-where-to-find-them.md |
| 20:25:39 | 200 | https://help.kalshi.com/en/articles/15410219-liquidity-provider-program.md |
| 20:25:47 | 200 | https://help.kalshi.com/en/articles/13823819-how-to-become-a-market-maker-on-kalshi.md |
| 20:25:53 | 200 | https://help.kalshi.com/en/articles/13823805-fees.md |
| 20:26:05 | 200 | /trade-api/v2/incentive_programs?status=active&limit=5 |
| 20:26:13 | 200 | /trade-api/v2/incentive_programs?status=active&type=volume&limit=2 |
| 20:26:20 | 200 | /trade-api/v2/series/KXBTC15M |
| 20:26:26 | 200 | /trade-api/v2/series/fee_changes?series_ticker=KXBTC15M&show_historical=true |
| 20:26:33 | 200 | /trade-api/v2/series/fee_changes |
| 20:26:39 | 200 | /trade-api/v2/series/fee_changes?show_historical=true |
| 20:26:49 | 200 | /trade-api/v2/markets?series_ticker=KXBTC15M&status=open&limit=1 |
| 20:27:03 | 200 | /trade-api/v2/markets/KXBTC15M-26NOV031530-30/orderbook?depth=4 |
| 20:27:16 | 401 | wss handshake to api.elections.kalshi.com/trade-api/ws/v2 without credentials |
| 20:27:49 | 200 | /trade-api/v2/account/endpoint_costs |

(The `/trade-api/v2/...` paths are on `https://api.elections.kalshi.com`.)
