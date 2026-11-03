# LLM forecasters and AI trading agents vs prediction-market prices (Kalshi, Polymarket, Manifold, Metaculus): research notes, 2026-11-03

> **How these notes were sourced.** The session proxy blocked full-text fetches from arxiv.org, metaculus.com, forecastingresearch.substack.com and proceedings.iclr.cc. It also blocked GitHub API reads of the bot repositories. Every number below therefore comes from search-engine extractions of the cited pages, not from reading the full papers. Treat all figures as unverified until they are checked against the primary PDF. Every reported return is a claim, not a verified result. Dates are given so older facts (before 2026) can be spotted.

## 1. What do forecasting benchmarks report as of 2026, and how do the best LLM systems compare with crowd or market forecasts, by question type and horizon?

### Takeaway
By mid-2026 the best LLM systems had reached rough parity with elite human forecasters on questions that are not traded markets. Examples are ForecastBench's dataset questions and Metaculus FutureEval, where the Pros' Spring 2026 lead of 1.25 points was not statistically significant. Against liquid market prices they still mostly lose or tie. The strongest LLM results on market questions come from models that were shown the market price. On Kalshi events (Prophet Arena), markets beat LLMs as resolution approaches. Parity with humans is not the same as beating the price.

### Cited Findings
**ForecastBench (Forecasting Research Institute, FRI)**
- **January 2026 snapshot:** superforecasters ranked first, ahead of the best LLMs by 0.017 Brier points (difficulty-adjusted), with external AI submissions second and third. Surveys projected parity around late 2026, and one projection from February 2026 said December 2026. Sources: [FRI, "LLMs are closing the gap"](https://forecastingresearch.substack.com/p/llms-are-closing-the-gap-on-human); [LEAP forecast page](https://leap.forecastingresearch.org/forecasts/forecastbench-performance). Taken from a search extraction; which source carries which number is approximate.
- **July 16, 2026 FRI post, "AI models have likely reached parity":**
  - several models are statistically indistinguishable from superforecasters on the tournament leaderboard;
  - the top system is from Cassi AI;
  - 17 submissions rank above superforecasters on the preliminary leaderboard of resolved dataset questions;
  - an AI system ranked above superforecasters on market questions for the first time.

  Source: [FRI](https://forecastingresearch.substack.com/p/ai-models-have-likely-reached-parity).
- **Contrary view from Good Judgment Inc.** (a superforecaster firm with a stake in the result; the analysis is undated and appears to predate the July post). It says superforecasters rank first overall and "hold a commanding lead on market questions (80.3 vs. 75.8 for the nearest AI)". It argues that resolved questions skew toward short-horizon, data-rich series where AI has structural advantages, that the superforecaster baseline is a one-time study from mid-2024, and that difficulty adjustment adds uncertainty. Sources: [GJ, What Superforecasters Actually Said](https://goodjudgment.com/what-superforecasters-actually-said-about-forecastbench/); [GJ, What ForecastBench Doesn't Measure (Yet)](https://goodjudgment.com/what-forecastbench-doesnt-measure/). A second extraction of GJ material instead gave "roughly 50% more accurate on market questions (0.40 vs 0.59)". The two scales are inconsistent and the conflict is unresolved.
- **Third-party report, May 2026:** superforecasters lead on market questions by 7.2 Brier Index points (78.6 against a figure 7.2 points lower). On dataset questions, the AI entrant "Green Tree" (64.6–64.8) exceeds the superforecaster median (63.6). The report says "comprehensive parity... has not been established as of late May 2026". Source: [Parallect](https://parallect.ai/reports/ai-superforecasters-forecastbench-may-2026-895525).
- **Method caveats:**
  - For unresolved market questions, ForecastBench scores forecasts against the platform's community aggregate rather than the outcome.
  - All of the top-performing LLMs had access to the crowd forecast on market questions.
  - A secondary summary gives about 0.122 Brier with crowd access and about 0.136 without.

  Sources: [ForecastBench paper, ICLR 2025](https://proceedings.iclr.cc/paper_files/paper/2025/file/ea74e45a229dac70b5b63b28d8934db6-Paper-Conference.pdf); [Foresight Arena related-work section](https://arxiv.org/pdf/2605.00420).

**Metaculus FutureEval (the AI Benchmarking series, launched under the new name in February 2026; [GlobeNewswire, February 18, 2026](https://www.globenewswire.com/news-release/2026/02/18/3239902/0/en/Metaculus-Launches-FutureEval-to-Track-AI-Forecasting-Accuracy.html))**
- **Spring 2026 (January 7 to April 15, 2026):** the bot team scored −1.25 head-to-head against the Pro team (95% CI −4.87 to +2.37; positive numbers mean bots beat Pros), so the Pro lead was not significant. The earlier seasons were −11.3 (Q3 2024), −8.9 (Q4 2024), −17.7 (Q1 2025) and −20.0 (Q2 2025). Sources: [Metaculus analysis on LessWrong](https://www.lesswrong.com/posts/wZBbDqzfBjYG58CxK/futureeval-spring-results-pros-beat-bots-but-the-gap-is); [Metaculus methodology](https://www.metaculus.com/futureeval/methodology/).
- **Spring 2026 detail:**
  - 173 bots competed (111 excluding Metaculus's own) on 297 scored questions, 99 of which had a direct Pro comparison;
  - Pros outscored bots on 64% of questions, but the bot wins were by larger margins;
  - 9 of the top 10 places on a combined leaderboard would be Pros;
  - it was the first season in which no Metaculus-run baseline bot reached the top 10.

  Source: [LessWrong](https://www.lesswrong.com/posts/wZBbDqzfBjYG58CxK/futureeval-spring-results-pros-beat-bots-but-the-gap-is).
- **Track record:** Pros have won every season so far ([FutureEval](https://www.metaculus.com/futureeval/)). A naive linear extrapolation has the single-prompt baseline bots beating Pros around June 2027; that is an extrapolation, not a result ([EA Forum, "AI Forecasting in 2026: What 11 Analyses Say"](https://forum.effectivealtruism.org/posts/Spyz3wESZu2eeqhDj/ai-forecasting-in-2026-what-11-analyses-say)).
- **Summer 2026 Metaculus Cup:** the bots Laertes and ManticAI reportedly finished first and second overall, and FutureSearch fifth. Bots are not eligible for prizes ([explainx.ai, secondary](https://explainx.ai/blog/ai-beats-forecasters-metaculus-cup-coverage-2026)).

**Prophet Arena (University of Chicago; live events taken from Kalshi)**
- **ICLR 2026 paper:**
  - 1,367 resolved events covering 72,136 binary markets, with about 20 new Kalshi events added per day;
  - category mix: 81% sports, 5% entertainment, 5% politics, 9% other;
  - GPT-5, Grok-4 and Claude Sonnet 4 scored Brier 0.18–0.22 (a random guess scores 0.25), described as "competitive with the market baseline";
  - markets "rapidly incorporate new information and outperform LLMs closer to resolution";
  - most AI forecasters beat the average Kalshi human on calibration and profit, but all are worse than the best humans.

  Sources: [ICLR 2026 paper](https://proceedings.iclr.cc/paper_files/paper/2026/file/aec5e2847c5ae90f939ab786774856cc-Paper-Conference.pdf); [alphaXiv](https://www.alphaxiv.org/abs/2510.17638).
- **Horizon results:** forecasts are made in lead-time bins (for example 0–3 hours, 1–2 days, more than 4 days). LLMs look relatively stronger at long horizons. Near-resolution forecasts mostly reflect real-time information access. GPT-5's average return was 0.943 against 0.899 for the market baseline, and even the top model stayed below break-even (1.0). Sources: [paper notes](https://en.papernotes.org/ICLR2026/llm_evaluation/llm-as-a-prophet_understanding_predictive_intelligence_with_prophet_arena/); [OpenReview](https://openreview.net/forum?id=Qj1ZcF42Gl).
- **Live leaderboard:** it scores 1 − Brier, with the "Kalshi Markets" baseline at 0.9460 across all events. The model entries came back garbled and are unverified ([Prophet Arena leaderboard](https://www.prophetarena.co/leaderboard/forecast)).

**KalshiBench (December 2025)**
- The benchmark uses 300 Kalshi questions that resolved after the models' training cutoffs, drawn from a full set of 1,531 (September 2021 to November 2025, 13 categories).
- The best-calibrated model was Claude Opus 4.5, with an expected calibration error (ECE) of 0.120. GPT-5.2-XHigh had ECE 0.395 despite comparable accuracy.
- Only one model had a positive Brier Skill Score against simply predicting base rates.

Sources: [arXiv 2512.16030](https://arxiv.org/pdf/2512.16030); [Hugging Face papers](https://huggingface.co/papers/2512.16030).

**Academic systems compared with crowds and markets**
- **Halawi et al.** (arXiv February 2024, NeurIPS 2024; older): a retrieval-based system scored Brier .179 against .149 for the crowd on the full test set, and was not consistently better than the crowd ([NeurIPS paper](https://proceedings.neurips.cc/paper_files/paper/2024/file/5a5acfd0876c940d81619c1dc60e7748-Paper-Conference.pdf)).
- **Schoenegger et al.** (Science Advances, 2024; older): an ensemble of 12 LLMs on 31 binary questions was statistically indistinguishable from a tournament crowd of 925 people. Earlier work by the same authors found a single GPT-4 could not beat a 50% baseline ([Science Advances](https://www.science.org/doi/10.1126/sciadv.adp1528)).
- **AIA Forecaster** (Bridgewater AIA Labs, November 2025): on MarketLiquid (1,610 questions from 322 liquid markets in policy, economics and technology), the system scored Brier 0.1258 against 0.1106 for the market, so the market was better. A mirror of the paper reports 0.108 (system), 0.098 (market) and 0.092 (ensemble), which looks like a different version. Sources: [arXiv 2511.07678](https://arxiv.org/pdf/2511.07678); [chatpaper mirror](https://chatpaper.com/paper/208492).
- **PolyBench** (April 2026): 38,666 Polymarket binary markets across 4,997 events. Seven LLMs made about 36,165 predictions on market states from February 6–12, 2026. Only 2 of the 7 had positive simulated returns: MiMo-V2-Flash at 17.6% confidence-weighted return and Gemini-3-Flash at 6.2% ([arXiv 2604.14199](https://arxiv.org/html/2604.14199v1)).
- **Hindcast** (May/July 2026): replays 216 resolved Polymarket markets against a frozen Reddit snapshot. Retrieval lowered Brier for 8 of 9 models (by up to 23%); it helped on Sports, Awards and Trading and hurt on Entertainment. The paper treats the market price as a strong baseline. It cites a related study in which "the best-performing LLM-based forecaster would perform better if it simply output the market price" ([arXiv 2607.14051](https://arxiv.org/html/2607.14051v1)).

### Inferences
- **Two yardsticks get conflated: humans and prices.** Against humans (Pros and superforecasters on Metaculus and ForecastBench), parity has nearly arrived. Against prices, the best evidence still shows the market at least as accurate as the LLM, and more accurate near resolution. That evidence is Prophet Arena, AIA on MarketLiquid, KalshiBench and Hindcast.
- **LLM wins over the market come with help.** Where an LLM beats the market on a benchmark, it usually either had the market price as an input or was ensembled with it. In those cases the LLM adds a small correction to the price; it does not replace it.
- **Horizon gradient.** The LLM's relative standing improves with time to resolution, and the market wins near resolution. A 15-minute contract sits at the far short end of this gradient.
- **Category.** Kalshi's flow is sports-dominated (81% of Prophet Arena events), and sports markets are among the most professionally priced. The LLM evidence there is weakest.
- **The gaps are small.** Reported differences are hundredths of a Brier point, so sampling noise can easily flip rankings in small tests (see section 7 for the desk's 74 forecasts).

### Gaps
- Full texts could not be fetched, so all numbers above are unverified.
- I found no current (November 2026) ForecastBench standings table and no Fall 2026 FutureEval results. The Fall 2026 tournament exists per [Metaculus PR #5205](https://github.com/Metaculus/metaculus/pull/5205).
- I could not verify which platforms supply ForecastBench's "market" questions. I believe they include play-money or aggregator platforms such as Manifold and Metaculus alongside Polymarket, but did not re-verify this. If so, "AI beats superforecasters on market questions" says little about beating real-money Kalshi prices.
- No benchmark measures LLMs on Kalshi's 15-minute crypto contracts.

## 2. Are there documented LLM or AI agents trading real money on Kalshi or Polymarket, and what were their results?

### Takeaway
Every controlled real-money test of LLM trading agents on Kalshi or Polymarket that I found lost money or roughly broke even. The large positive returns that exist are self-reported, simulated, or drawn from very short windows. The one documented profitable real-money bot is a non-LLM market maker whose profit came from maker rebates, not from forecasting.

### Cited Findings
- **Prediction Arena** (arXiv 2604.07355, April 2026): frontier models traded real money on Kalshi and Polymarket, January to March 2026. The models lost between 16% and 30.8% of their capital on Kalshi. On Polymarket, "Cohort 1" averaged −1.1%. In Kalshi phase 1, one model settled 51.9% of its markets correctly against 15.4% for another ([arXiv](https://arxiv.org/html/2604.07355v1)). One secondary summary describes the main live window as about five weeks; the exact duration is unverified.
- **Cybernews on the same study:** every live-trading frontier model lost money over the full evaluation period, and the only strong positive return was a paper-trading run with simulated money. The headline says the researchers "lost $3,000" ([Cybernews](https://cybernews.com/ai-news/viral-ai-trading-debunk-model-lost-money-polymarket-kalshi/)).
- **PredictionMarketBench** (arXiv 2602.00133, February 2026; replays historical markets): a tool-calling LLM agent (gpt-4.1-nano) and a random agent both "suffered from transaction costs and settlement losses", while fee-aware algorithmic strategies stayed competitive ([arXiv](https://arxiv.org/html/2602.00133v1)).
- **"When do prophets profit in prediction markets?"** (Gu, Kagan, Sun; University of Chicago, linked to Prophet Arena; arXiv 2607.06166, July 2026): a month-long Kalshi deployment reportedly returned +80.33% with a Sharpe ratio of 3.35. This is self-reported by the benchmark's own team and unverified ([arXiv](https://arxiv.org/abs/2607.06166); [Prophet Arena write-up](https://www.prophetarena.co/research/when-do-prophets-profit)).
- **Polymarket's official agents framework** (github.com/Polymarket/agents): infrastructure only, covering API connections, order management, position tracking and retrieval-augmented data. I found no independent accuracy or P&L benchmark of it ([Semantic Trading paper, related work](https://arxiv.org/html/2512.02436v1); [X post noting about 1.6k stars](https://x.com/LiorOnAI/status/2014413098979897579?lang=en)).
- **Olas / Valory "Polystrat" agents on Polymarket** (company claims): more than 4,200 trades within about a month of launch, single-trade returns up to 376%, and more than 37% of agents with positive P&L (which implies most were not positive). Valory's founder said off-the-shelf prompting is "no better than a coin-flip", while custom workflows reach "accuracy up to 70% and higher". Source: [CoinDesk, March 15, 2026](https://www.coindesk.com/tech/2026/03/15/ai-agents-are-quietly-rewriting-prediction-market-trading); which outlet carried which claim is approximate.
- **Medium critique of platform claims:** "actual prediction accuracy is 67%, not the 94%" self-reported, and the self-reported figure is measured one month before resolution. It calls survivorship bias in reported results "severe" ([Medium](https://fglancszpigel.medium.com/debunking-the-polymarket-dream-d67ba3922e4b); a blog post).
- **Semantic Trading** (arXiv 2512.02436, December 2025): LLM agents that cluster and link related Polymarket markets found relationships with about 60–70% accuracy. The trading strategies built on those links averaged about 20% return over week-long horizons, an unverified backtest-style figure ([arXiv](https://arxiv.org/html/2512.02436v1)).
- **Alpha Arena (Nof1)** traded live crypto perpetuals, not prediction markets. Season 1 ran October 18 to November 3, 2025 (older). Qwen3 Max returned about +22.3% and DeepSeek Chat V3.1 about +4.9%; the other four models lost. GPT-5 lost more than 60% (−62.7% per one source). Nof1 said trading costs ate into results and that the season was small, short and "may have been luck" ([iWeaver summary](https://www.iweaver.ai/blog/alpha-arena-ai-trading-season-1-results/)). In Season 1.5 (US stocks), one source reports all models lost overall ([BigGo Finance](https://finance.biggo.com/news/5BSX_Z0BaoGGrU-ID27J); [OneDayAdvisor](https://www.onedayadvisor.com/2025/12/nof1ai-alpha-arena-review-season-15.html)).
- **Non-LLM real-money market-making bot on Polymarket US** (September to October 2026), using Kalshi prices as its fair value. Over 44 days it earned $52.53 in maker rebates and $11.36 in liquidity rewards, while trading itself made only +$4.75 ([GitHub Tanuj-07/polymarket-market-making](https://github.com/Tanuj-07/polymarket-market-making)).
- **Kalshi 15-minute crypto:**
  - an open live-research repository reported −$240 on 993 trades at the time indexed ([GitHub Kalshibot98/kalshi15](https://github.com/Kalshibot98/kalshi15));
  - a vendor test that let an LLM choose buy YES, buy NO or skip each minute lost $10.71 over 54 windows after Kalshi fees, within noise for that sample ([botforkalshi](https://www.botforkalshi.com/blog/kalshi-bitcoin-bot)).
- **Marketing claims without verified results:** for example, a self-hosted agent "built on Claude" claiming to trade "1000+ markets" ([GitHub CloddsBot](https://github.com/alsk1992/CloddsBot)).
- **Competition is rising:** the trade press reports that "easy money" on Polymarket and Kalshi is disappearing as proprietary trading firms deploy AI agents ([CryptoSlate](https://cryptoslate.com/easy-money-on-polymarket-and-kalshi-is-disappearing-as-prop-firms-deploy-ai-agents/)).

### Inferences
- **Independent tests are negative; positive results are not.** The pattern is consistent: Prediction Arena (live), PolyBench (5 of 7 models lose), PredictionMarketBench, Alpha Arena and the 15-minute crypto tests all lose or break even. The positive figures come from the authors' own deployment (+80%), company data (Olas), simulation (PolyBench, paper trading) or tiny samples.
- **Kalshi went worse than Polymarket.** Prediction Arena's models lost much more on Kalshi (−16% to −31%) than on Polymarket (about −1%). That fits Kalshi's per-trade taker fee (see section 4), but the paper's breakdown by cause was not readable, so this is an inference.
- **The money that is made is microstructure money.** The only verifiable real-money profit came from rebates and liquidity rewards to a non-LLM maker that used another venue's price as fair value. Profitable automation on these venues looks like maker, arbitrage or latency trading, not LLM judgment.

### Gaps
- I found no Kalshi-built AI trading tool with any published performance data.
- I could not read Prediction Arena's method (bet sizing, fee handling, trade counts, per-model breakdown) or the GitHub READMEs, because both hosts were blocked.
- I could not verify how the +80.33% Kalshi deployment was sized, how many markets it covered, or which categories.

## 3. Does combining an LLM forecast with the market price beat either alone, and what does the aggregation literature say about extremizing versus shrinking?

### Takeaway
Yes, but only in one form. The combination has to be anchored on the market: the LLM gets a small weight, fitted on held-out data. That weight was about 20% in Halawi et al. and about one-third in the AIA report. The gains are small, on the order of −0.003 to −0.005 Brier.

The theory says three things:
- A plain linear average of forecasts is provably underconfident.
- Averaging noisy forecasts pulls toward 50%.
- Extremizing is justified only when the sources hold independent information. It is not justified when the LLM has already seen the market price or the same data.

No source supports a fixed 50/50 blend that leaves the market out.

### Cited Findings
**Empirical results for LLM plus crowd or market**
- **Halawi et al.** (2024, older): a weighted average with 4× weight on the crowd (picked on a validation set; the LLM weight is therefore 0.2) improved the overall Brier from .149 to .146. On questions where the crowd sat between .3 and .7, the crowd's Brier of .24 fell to .233 with the blend ([NeurIPS paper](https://proceedings.neurips.cc/paper_files/paper/2024/file/5a5acfd0876c940d81619c1dc60e7748-Paper-Conference.pdf); [arXiv](https://arxiv.org/pdf/2402.18563)).
- **AIA Forecaster** (November 2025):
  - On MarketLiquid, where the market beat the LLM, a simplex-constrained regression of the outcome on the market price and the LLM forecast gave the LLM about one-third of the weight. The leave-one-out ensemble beat both inputs (about 0.106 per secondary write-ups, against 0.1106 for the market).
  - On ForecastBench's market subset, by contrast, "the market price does *not* provide signal that is additive" to the LLM.
  - Giving the market price to the LLM as an input improved its score from 0.085 to 0.075.

  Sources: [arXiv 2511.07678](https://arxiv.org/pdf/2511.07678); [alphaXiv](https://www.alphaxiv.org/abs/2511.07678).
- **ForecastBench:** the top LLMs on market questions all had access to the crowd forecast ([ForecastBench paper](https://proceedings.iclr.cc/paper_files/paper/2025/file/ea74e45a229dac70b5b63b28d8934db6-Paper-Conference.pdf)).
- **Hindcast:** treats the market price as the prior and cites a study in which the best LLM forecaster would have done better by outputting the market price ([arXiv 2607.14051](https://arxiv.org/html/2607.14051v1)).
- **"Beyond Accuracy: Can LLM Forecasters Profit on Prediction Markets?"** (OpenReview, undated, around 2025–2026):
  - The strongest single LLM achieved "accuracy statistically indistinguishable from the market while earning significantly higher realized returns". Its edge "comes entirely from losing less when wrong".
  - "Conditioning first on crowd agreement yields significantly higher Sharpe ratio, portfolio ROI, and average PnL than either the unfiltered LLM forecaster or the market baseline."
  - The paper splits profit into an "accuracy channel" (how often you are right) and a "price-paid channel" (how much you pay for your bets).

  Sources: [OpenReview](https://openreview.net/forum?id=TSA5kRUKZv); [Lacuna summary](https://lacuna.tiptreesystems.com/work/beyond-accuracy-can-llm-forecasters-profit-on-prediction-markets/wrk_58f2322089a110fc5d773e7231e0dd88).
- **"When do prophets profit"** (July 2026):
  - It builds a "proper" betting strategy that uses only the forecaster's prediction and the market price.
  - It extends the theory linking accuracy to profit from automated market makers to central limit order books.
  - A forecaster can profit even with worse accuracy than the market if bet size and direction capture the divergence and liquidity allows.
  - Across thousands of AI forecasts, proper betting was "the only strategy that reliably turned accuracy into profit".
  - It cites a NeurIPS 2025 workshop paper titled "The losing winner".

  Source: [arXiv 2607.06166](https://arxiv.org/abs/2607.06166).
- **"Beyond Forecasting: The Belief-to-Trade Layer"** (Raven-Agent; arXiv 2607.03015, July 2026): a trading layer placed after a swappable forecaster ranks candidates by a time-normalized return, sizes at one-quarter Kelly and enforces hard stake, exposure, stop-loss and drawdown limits. In a controlled replay it produced "the only positive return and the only positive risk-adjusted return among all tested policies". The authors call the results preliminary, and positions are held to resolution ([arXiv](https://arxiv.org/abs/2607.03015); [Pith summary](https://pith.science/paper/2607.03015)).

**Aggregation theory: shrinking, pooling, extremizing**
- **Ranjan & Gneiting (2010, Journal of the Royal Statistical Society B; older):** any non-trivial weighted linear average of two or more distinct, calibrated forecasts is uncalibrated and lacks sharpness. Linear pooling needs recalibration "even in the ideal case" of calibrated inputs, and they propose a beta-transformed linear pool ([EconPapers](https://econpapers.repec.org/RePEc:bla:jorssb:v:72:y:2010:i:1:p:71-91)). Gneiting & Ranjan (2013) show the traditional linear pool is not "flexibly dispersive" ([Electronic Journal of Statistics](https://projecteuclid.org/journals/electronic-journal-of-statistics/volume-7/issue-none/Combining-predictive-distributions/10.1214/13-EJS823.full)). The pool's parameters can be fitted by maximum likelihood ([forecast-combination review, arXiv 2205.04216](https://arxiv.org/pdf/2205.04216)).
- **Baron et al. (2014, Decision Analysis; older):** "Two Reasons to Make Aggregated Probability Forecasts More Extreme". One reason is that random error pulls averaged probabilities toward 0.5, because the probability scale is compressed near its ends ([EconPapers](https://econpapers.repec.org/RePEc:inm:ordeca:v:11:y:2014:i:2:p:133-145)).
- **Satopää et al. (2014, International Journal of Forecasting; older):** a logit model that extremizes the average log-odds. In Satopää and Pemantle's information-diversity framing, the optimal amount of extremizing depends on how much the forecasters' information overlaps ([arXiv 1406.2148](https://arxiv.org/abs/1406.2148v2); [EconBiz](https://www.econbiz.de/Record/two-reasons-to-make-aggregated-probability-forecasts-more-extreme/10010382759)).
- **Neyman, "Algorithmic Bayesian Epistemology" (2024):** if the experts' evidence is "identical or heavily overlapping", averaging is sensible. If it is "heavily non-overlapping", the usual pools are "insufficiently extremizing", and pooling then extremizing is the state of the art. A logarithmic pool takes confident forecasts "more seriously" than a linear pool ([arXiv 2403.07949](https://arxiv.org/pdf/2403.07949)).
- **Averaging log-odds** (the geometric mean of odds) always gives more extreme pooled probabilities than averaging probabilities. Dependence between events can break it ([EA Forum, "When pooling forecasts, use the geometric mean of odds"](https://forum.effectivealtruism.org/posts/sMjcjnnpoAQCcedL2/when-pooling-forecasts-use-the-geometric-mean-of-odds)).
- **Extremizing can backfire:** applying a linear-in-log-odds transform to an average on the wrong side of 0.5 "has the potential of pushing the forecast away from the true probability" ([NYU Abu Dhabi working paper, 2024](https://nyuad.nyu.edu/content/dam/nyuad/academics/divisions/social-science/working-papers/2024/WP%200102.pdf)).
- **Opposing forecasts cancel:** a normalized geometric (log) pool of two opposing sharp forecasts, [0.9, 0.1] and [0.1, 0.9], gives [0.5, 0.5], which is less sharp than either input ([GitHub issue, microprediction/mechanisms](https://github.com/microprediction/mechanisms/issues/14)).
- **Tammet, Järv & Draheim (arXiv 2608.11275, August 2026):** each pooling rule is exact only in its own generative "world". Averaging suits cases where one of several alternative interpretations applies. Multiplying odds suits conditionally independent evidence with a common prior. Numerically different rules can still give the same decision at a 1/2 threshold ([arXiv](https://arxiv.org/abs/2608.11275)).

### Inferences
**The best-supported recipe is "the market price plus a fitted, shrunken LLM deviation"**
- **Linear form:** q = m + w·(L − m), where m is the market mid, L is the LLM's forecast and w is fitted out of sample.
- **Log-odds form:** logit(q) = a + b_m·logit(m) + b_L·logit(L). This is a generalized log pool, and it permits extremizing only if the data say so.
- **Where the weight should come from:** the weight is the slope of a "disagreement regression" of (outcome − m) on (L − m). Its interpretation:
  - w = 0 means the LLM adds nothing;
  - 0 < w < 1 says how far to shrink the LLM toward the market;
  - w > 1 would mean the LLM is underconfident relative to the market, which is rare.
- **Where the observed weights apply:** the published weights (0.2 and about 0.33) come from longer-horizon event questions where retrieval adds information. On short-horizon price contracts the fitted w should be expected to sit near 0.

**Shrinking against extremizing**
- Shrink the LLM toward the market. LLMs are overconfident (section 5), and their information overlaps heavily with the market's, especially when they are shown the price.
- Do not extremize an LLM-plus-market pool unless the LLM brings information the market lacks; the overlap theory says the extremizing factor should then be close to 1.
- Extremizing the market price itself toward 0 and 1 in the tails is a separate idea, discussed in sections 5 and 6.
- **What a linear blend does:** a 50/50 average of two inputs that are each less informative than the market loses resolution. By Ranjan–Gneiting and Baron, it is also pulled toward 50%.

**Accuracy against profit**
- Small Brier gains can in principle pay. If the pooled forecast q is calibrated, the expected profit from buying at price m is q − m. A Brier gain of 0.004 means the market's mean squared mispricing is at least 0.004, an average error of about 6 cents. My algebra: Brier(m) − Brier(q) = MSE(m) − MSE(q) when the outcome's true probability is p.
- That only becomes profit if the trades are restricted to deviations larger than fee + half-spread, and sized properly (proper betting, fractional Kelly).

**Using the LLM only to flag disagreements**
- This is the lowest-risk use. Price comes from the market, and the LLM triggers investigation or a veto.
- The "Beyond Accuracy" crowd-agreement filter is indirect support. Its exact definition could not be read; see Gaps.

**Sample size to estimate w (my calculation)**
- The standard error of w is about sqrt(Brier_m / (n · Var(L − m))).
- With a market Brier of about 0.18 and the LLM typically 8 points from the market (SD 0.08), n = 74 gives SE(w) ≈ 0.62.
- Reaching SE 0.1 takes about 2,800 resolved forecasts, or about 800 if the typical deviation is 15 points.

### Gaps
- I found no published study of pooling an LLM with the market on Kalshi short-horizon contracts.
- The exact definition of "conditioning first on crowd agreement" in "Beyond Accuracy" could not be read. It is unclear whether it means trading only when the LLM agrees with the market's favored side.
- I did not verify the classic finding that properly aggregated prediction polls can match or beat prediction markets (Atanasov et al., 2017) this session.
- No source quantified how much of the AIA ensemble gain survives fees and spreads.

## 4. On fast markets such as 15-minute crypto contracts versus slow event markets, where do LLMs have any comparative advantage?

### Takeaway
LLMs have no demonstrated advantage on 15-minute crypto contracts:
- the relevant information is public price data;
- cross-venue price discovery happens in milliseconds;
- measured directional edges are smaller than Kalshi's taker fee;
- an LLM takes seconds to answer.

Whatever comparative advantage LLMs have is on slower, text-heavy event questions at longer horizons, and even there it shows up mainly as a correction to the market price.

### Cited Findings
- **Horizon:** Prophet Arena finds markets beat LLMs closer to resolution, while LLMs are relatively stronger at long horizons ([ICLR 2026 paper](https://proceedings.iclr.cc/paper_files/paper/2026/file/aec5e2847c5ae90f939ab786774856cc-Paper-Conference.pdf); [paper notes](https://en.papernotes.org/ICLR2026/llm_evaluation/llm-as-a-prophet_understanding_predictive_intelligence_with_prophet_arena/)).
- **OpenMarket** (arXiv 2607.26245, July 2026), a dataset of Polymarket's BTC 15-minute order books paired with Binance BTC/USDT trades:
  - 2,936,031 matched event pairs over 93 days (February 12 to May 15, 2026), covering 4,450 markets;
  - Polymarket book events trail Binance by a median of 16 ms (5th–95th percentile −186 to +316 ms);
  - measured on the collector's own clock, quotes follow large Binance moves with a median lag of 347 ms;
  - the books are usually one tick wide at the top;
  - multivariate features "slightly underperform the naive mid prior out-of-sample".

  Sources: [arXiv](https://arxiv.org/html/2607.26245v1); [GitHub openmarket](https://github.com/gregyoung14/openmarket).
- **Vendor study of 6,298 settled KXBTC15M windows** (KXBTC15M is Kalshi's 15-minute bitcoin series): the leading side was worth about 0.67¢ per contract before costs, against an average taker fee of about 1.55¢. The vendor also warns that paper results do not reproduce live fills, latency, rejections or all execution costs ([botforkalshi, KXBTC15M strategy data](https://www.botforkalshi.com/blog/kalshi-15-minute-bitcoin-markets); [botforkalshi, bitcoin bot](https://www.botforkalshi.com/blog/kalshi-bitcoin-bot)).
- **Latency:** a vendor measured a Binance feed median of 1.45 ms and a Kalshi feed median of 9.4 ms ([CryptoStruct latency guide](https://cryptostruct.com/guides/prediction-market-bot-latency)). A GitHub bot claims a multi-second Kalshi lag behind Binance; that is the author's assertion, contradicted by the vendor figures above. Another repository puts Binance about 1 second ahead of the CF Benchmarks BRTI index "that settles these contracts". Which repository said which is uncertain: [kalshibot](https://github.com/brandononchain/kalshibot) or [Kalshi-CryptoBot](https://github.com/Bh-Ayush/Kalshi-CryptoBot).
- **Market context:** short-term crypto contracts are more than half of crypto trading on Polymarket and Kalshi, and Polymarket added per-trade fees on 15-minute crypto contracts to curb bots. Which outlet carried this is uncertain: [MEXC news](https://www.mexc.com/news/923042) or [botforkalshi](https://www.botforkalshi.com/blog/kalshi-15-minute-bitcoin-markets).
- **Real tests on 15-minute contracts:** −$240 on 993 trades ([Kalshibot98/kalshi15](https://github.com/Kalshibot98/kalshi15)); an LLM choosing YES, NO or skip each minute lost $10.71 over 54 windows ([botforkalshi](https://www.botforkalshi.com/blog/kalshi-bitcoin-bot)).
- **LLMs and time series** (Tan et al., NeurIPS 2024; older): removing the LLM component from three LLM-based time-series forecasters, or replacing it with a basic attention layer, "does not degrade forecasting performance" ([NeurIPS](https://proceedings.neurips.cc/paper_files/paper/2024/hash/6ed5bf446f59e2c6646d23058c86424b-Abstract.html)).
- **Kalshi fees:**
  - taker fee = round up(0.07 × C × P × (1 − P)) to the next cent, where C is the number of contracts and P the price in dollars;
  - maker fees use a 0.0175 rate and apply only on series designated for maker fees;
  - at 50¢, 100 contracts pay $1.75 as taker and about $0.44 as maker.

  Sources: [DeFi Rate](https://defirate.com/learn/prediction-market-fees/); [BettingUSA](https://www.bettingusa.com/prediction-markets/reviews/kalshi/fees/). One secondary source ties the current schedule to July 7, 2026 and a per-series multiplier ([chudi.dev](https://chudi.dev/blog/kalshi-fees); not verified against Kalshi's own fee PDF).
- **Where retrieval helps slow markets:** retrieval helps LLMs on Sports, Awards and Trading questions and hurts on Entertainment, where "speculative hype reads as evidence" ([Hindcast](https://arxiv.org/html/2607.14051v1)). LLM help to a crowd was largest where the crowd was uncertain, priced between .3 and .7 ([Halawi et al.](https://proceedings.neurips.cc/paper_files/paper/2024/file/5a5acfd0876c940d81619c1dc60e7748-Paper-Conference.pdf)). The one documented ensemble gain over a liquid market was on policy, economics and technology questions ([AIA](https://arxiv.org/pdf/2511.07678)).
- **Where AI matches humans:** AI's parity with superforecasters is concentrated on short-horizon, data-rich ForecastBench dataset questions (Good Judgment's argument; [GJ](https://goodjudgment.com/what-forecastbench-doesnt-measure/)). Those questions are compared with humans, not with a traded price.

### Inferences
**Comparative-advantage ranking, from least to most plausible for LLMs**
1. 15-minute or hourly crypto: the price is close to a random walk, the information is public, latency rules, and the fee is at its maximum near 50¢.
2. Sports: professionally priced, with fast news.
3. Scheduled economic releases: well covered by consensus forecasts and professionals.
4. Long-dated, rule-heavy, low-attention politics, policy and technology markets. Here an LLM's reading and synthesis may add information the marginal trader lacks.

Even in (4), the evidence supports the LLM as a shrunken correction to the price. The cost there is wide spreads, thin size and capital locked until resolution.

**On 15-minute crypto the right benchmark is the market mid**
- The edges that exist are microstructure edges: stale-quote pickoffs, market making with rebates and cross-venue lead-lag. They are measured in milliseconds, which an LLM taking seconds cannot reach.
- Any LLM decision made seconds after a quote is snapshotted risks adverse selection when it crosses the spread.

**Fee arithmetic (my calculation from the formula above)**
- Rounding up per order makes small orders costlier. One contract at 50¢ pays 2¢ (nominal 1.75¢); one contract at 90¢ pays 1¢ (nominal 0.63¢).
- A taker strategy at mid-range prices therefore needs about 2–3¢ of true edge per contract, including half the spread, just to break even.

### Gaps
- I found no peer-reviewed study of LLMs on Kalshi's 15-minute contracts; the evidence is vendor and hobbyist tests.
- I did not verify KXBTC15M settlement mechanics: whether the contract settles on a single BRTI print or an average over the final minute, and its exact timing. This matters for any lognormal formula (section 7).
- I did not verify Kalshi's current maker-fee designation for crypto series.

## 5. What are the known failure modes (overconfidence, poor tail calibration, hedging toward 50 percent, data leakage in backtests)?

### Takeaway
The documented LLM failure modes are:
- overconfidence, which is worse in reasoning-heavy models;
- an upward "acquiescence" skew;
- forecasts that piggyback on crowd or market forecasts;
- leakage-contaminated backtests;
- accuracy that does not turn into profit after costs.

I found no source showing that LLMs as such hedge toward 50%. The documented pull toward 50% comes from linear averaging of disagreeing or noisy forecasts. On Kalshi, a pull toward 50% is especially costly because cheap longshot contracts are already overpriced.

### Cited Findings
- **Overconfidence:** reasoning-enhanced GPT-5.2-XHigh had ECE 0.395 against 0.120 for the best model (Claude Opus 4.5), and only one model beat predicting base rates on Brier Skill Score. "Scaling and enhanced reasoning do not automatically confer calibration benefits" ([KalshiBench, arXiv 2512.16030](https://arxiv.org/pdf/2512.16030)).
- **Acquiescence skew:** the 12-LLM ensemble's mean forecast was 57.35% (SD 20.93), significantly above 50%, even though the questions resolved almost evenly. The authors tie this to the human acquiescence bias ([Schoenegger et al., Science Advances 2024](https://www.science.org/doi/10.1126/sciadv.adp1528); [PMC full text](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC11800985/)).
- **Averaging pulls toward 0.5:** random error pulls averaged probabilities toward 0.5 ([Baron et al. 2014](https://econpapers.repec.org/RePEc:inm:ordeca:v:11:y:2014:i:2:p:133-145)), and linear pools of calibrated forecasts are uncalibrated and less sharp ([Ranjan & Gneiting 2010](https://econpapers.repec.org/RePEc:bla:jorssb:v:72:y:2010:i:1:p:71-91)).
- **Confidence without profit:** five of seven PolyBench models "lost money despite high stated confidence" ([PolyBench](https://arxiv.org/html/2604.14199v1)). Forecasters who beat the market on average "routinely fail to convert that edge into trading profit" ([When do prophets profit](https://arxiv.org/abs/2607.06166)). Prophet Arena's top model stayed below break-even ([paper notes](https://en.papernotes.org/ICLR2026/llm_evaluation/llm-as-a-prophet_understanding_predictive_intelligence_with_prophet_arena/)).
- **Leakage in backtests** (Paleka et al., arXiv 2506.00723, ICLR 2026):
  - "logical leakage": a model that knows the evaluation date can deduce an outcome;
  - date-restricted retrieval is unreliable, because of bad metadata, inaccurate date limits, search ranking shaped by future data, and retrieval models trained on future data;
  - filtering out contradictory older evidence overstates skill;
  - stated knowledge cutoffs cannot be trusted;
  - LLMs may piggyback on crowd forecasts present in training data or retrieved inputs;
  - in one dataset, at least 3.8% of questions had "early resolution".

  Suggested fixes are frozen indexes, robust date filtering and point-in-time practices borrowed from financial backtesting. Sources: [arXiv](https://arxiv.org/abs/2506.00723); [ICLR paper notes](https://en.papernotes.org/ICLR2026/llm_evaluation/pitfalls_in_evaluating_language_model_forecasters/).
- **Live-web retrieval:** it turns backtests into tests of fact retrieval rather than forecasting, and Hindcast proposes temporally controlled retrieval instead ([Hindcast](https://arxiv.org/html/2607.14051v1)). Live benchmarks avoid the problem because events are tracked before they resolve ([Prophet Arena, alphaXiv](https://www.alphaxiv.org/abs/2510.17638)).
- **Benchmark gaming:** correlated bets, skewed question distributions and imperfect metrics ([Paleka et al.](https://arxiv.org/abs/2506.00723)). The resolved ForecastBench questions skew toward short-horizon, data-rich questions ([GJ](https://goodjudgment.com/what-forecastbench-doesnt-measure/)).
- **Execution and reporting failures:**
  - paper results do not reproduce live fills, latency, rejections or all costs ([botforkalshi](https://www.botforkalshi.com/blog/kalshi-bitcoin-bot));
  - survivorship bias in reported agent results is "severe", and accuracy is self-reported a month before resolution ([Medium critique](https://fglancszpigel.medium.com/debunking-the-polymarket-dream-d67ba3922e4b));
  - Alpha Arena's results were eaten by trading costs ([iWeaver](https://www.iweaver.ai/blog/alpha-arena-ai-trading-season-1-results/));
  - an LLM agent lost to transaction costs and settlement losses like a random agent ([PredictionMarketBench](https://arxiv.org/html/2602.00133v1)).
- **Favorite-longshot bias on Kalshi** (Bürgi, Deng & Whelan; CEPR DP20631 / CESifo 2026 working paper):
  - over 300,000 contracts studied;
  - contracts priced below 10¢ win "far less often" than break-even requires and produce "very large average losses";
  - high-priced contracts win more often and earn small positive returns in some ranges;
  - takers lose about 32% on average against about 10% for makers (whether this average covers all contracts or longshots is unclear in the extraction);
  - the authors attribute the bias to fees, Kalshi's quote-driven structure and a tendency to overestimate small probabilities.

  Sources: [Whelan PDF](https://www.karlwhelan.com/Papers/Kalshi.pdf); [CEPR DP20631](https://cepr.org/publications/dp20631); [VoxEU column](https://cepr.org/voxeu/columns/economics-kalshi-prediction-market).

### Inferences
- **Tails are doubly dangerous.** LLMs are overconfident, and Kalshi longshots are already overpriced. An LLM that says a 5¢ contract is "really 15%" is most likely wrong, and buying it as a taker is the worst-returning trade type documented on Kalshi.
- **A pull toward 50% is a longshot-buying machine.** Any forecast that is systematically closer to 50% than the market makes the cheaper side look underpriced. It therefore steers trades into the overpriced longshot side.
- **Piggybacking breaks independence.** An LLM shown the market price or a model probability produces a forecast correlated with those inputs. Its "skill" against a base rate can look good while it adds nothing against the market, and pooling theory then says averaging or extremizing it with those same inputs adds little.
- **Leakage-free means forward-only.** For trading, the only leakage-free LLM test is prospective. Questions are asked live, answers are logged before resolution, and outcomes are scored later against the market price at the time.

### Gaps
- I found no source measuring LLM calibration specifically in the tails (below 10% or above 90%) against market prices.
- I found no source showing that LLMs, without being anchored, hedge toward 50% on short-horizon numeric questions. Whether a given model does so has to be measured in-house.
- I did not verify whether Kalshi's favorite-longshot bias holds within crypto 15-minute series; the study pools many categories.

## 6. Approach by approach: what it is, mechanism, evidence, soundness, requirements, paper-testability, and confidence in a durable after-fee edge on Kalshi

### Takeaway
No LLM approach has strong independent evidence of a durable after-fee edge on Kalshi. The most defensible are:
- market-anchored pooling on slow event markets (about 12% confidence);
- LLM-assisted consistency or semantic arbitrage between related markets (about 12%).

Treating the LLM as the probability source on 15-minute crypto has a confidence of about 1%. The literature's strongest pricing signal on Kalshi is a non-LLM one: the favorite-longshot bias.

### Cited Findings
- **Accuracy gains from market-anchored ensembles:** .149 to .146 with an LLM weight of 0.2 ([Halawi](https://proceedings.neurips.cc/paper_files/paper/2024/file/5a5acfd0876c940d81619c1dc60e7748-Paper-Conference.pdf)); about 0.1106 to about 0.106 with a weight of about one-third ([AIA](https://arxiv.org/pdf/2511.07678)).
- **Standalone LLMs against Kalshi prices:** average return below break-even ([Prophet Arena](https://en.papernotes.org/ICLR2026/llm_evaluation/llm-as-a-prophet_understanding_predictive_intelligence_with_prophet_arena/)); real-money Kalshi losses of 16% to 30.8% ([Prediction Arena](https://arxiv.org/html/2604.07355v1)).
- **Self-reported positive results:** +80.33% in a month on Kalshi with proper betting ([When do prophets profit](https://arxiv.org/abs/2607.06166)); about 20% weekly from strategies built on market relationships ([Semantic Trading](https://arxiv.org/html/2512.02436v1)); the only positive return in a replay ([Belief-to-Trade](https://arxiv.org/abs/2607.03015)).
- **Fees:** the taker fee is 0.07·P·(1 − P) per contract, rounded up, and the maker rate is 0.0175 on designated series ([DeFi Rate](https://defirate.com/learn/prediction-market-fees/)). Kalshi's favorite-longshot bias is reported by Bürgi, Deng & Whelan ([Whelan PDF](https://www.karlwhelan.com/Papers/Kalshi.pdf)).

### Inferences
Confidence is my subjective probability that the approach has a real edge after Kalshi fees that lasts at least 6–12 months at a small desk's scale.

| # | Approach | Confidence |
|---|---|---|
| A | LLM as a standalone probability source, slow event markets, taker | 5% |
| B | LLM as a standalone probability source, 15-minute crypto | 1% |
| C | Fixed 50/50 linear blend of LLM and formula, market excluded | <1% |
| D | Market-anchored pooling (LLM deviation shrunk by a fitted weight), slow event markets | 12% |
| E | Market-anchored pooling, 15-minute crypto | 2% |
| F | LLM as disagreement flag or triage, with rules or a human deciding (slow markets) | 10% |
| G | LLM as veto or risk filter on fast markets | 3% as an edge source |
| H | Extremizing an LLM-plus-market pool | 3% |
| I | Autonomous LLM trading agent (the Polymarket-agents or Prediction Arena style) | 3% |
| J | Proper-betting or fractional-Kelly layer on an LLM forecaster | 8% at system level |
| K | LLM-assisted semantic or consistency arbitrage across related markets | 12% |
| L | Ensemble of several LLMs as the forecaster | 4% |
| M | Non-LLM: recalibrate the market price toward the extremes (favorite-longshot), maker side | 25% (outside this note's scope) |

**A. LLM as a standalone forecaster, slow event markets, taker execution**
- **What it is:** an LLM, with retrieval, outputs a probability, and the desk trades when it beats the ask or bid by more than costs.
- **Mechanism:** the LLM synthesizes news and base rates better than the marginal trader in low-attention markets.
- **Evidence:** Brier is competitive with the market, but even the best model's average return is below break-even (Prophet Arena). Live Kalshi losses were 16–31% (Prediction Arena). Models are overconfident (KalshiBench). Alone, the LLM is worse than liquid markets (AIA 0.1258 vs 0.1106).
- **Is the logic sound?** Only for genuinely neglected markets. In general it is unsound: other traders also have LLMs, and an overconfident model's disagreements are mostly noise.
- **Needs to run:** an LLM with date-disciplined retrieval, bid/ask and depth data, a resolution tracker and a fee model. Capital is locked until resolution.
- **Paper testing:** forward paper trading is leak-free but slow, since each forecast waits for resolution. Fills on thin books are optimistic, and backtests on resolved markets are leakage-prone (Paleka et al.).
- **Confidence:** 5%.

**B. LLM as a standalone forecaster on 15-minute crypto, the desk's current setup**
- **What it is:** the LLM forecasts whether spot ends above the strike, or its direction, in the minutes left.
- **Mechanism:** none plausible. The price is close to a random walk, the information is public, and discovery takes milliseconds.
- **Evidence:** LLM components add nothing in time-series forecasting (Tan et al.). Markets dominate near resolution (Prophet Arena). The measured edge of 0.67¢ is below the 1.55¢ average fee (vendor). LLM tests lost money (−$10.71 over 54 windows). In OpenMarket, the naive mid beat 43-feature models out of sample.
- **Is the logic sound?** No.
- **Needs to run:** fast quotes. The LLM's latency is the binding problem.
- **Paper testing:** honest enough for accuracy, since outcomes arrive every 15 minutes. Taker fills are fine at small size if the ask is taken at decision time plus LLM latency. Detecting a 1¢ edge still needs about 10,000 trades (section 7).
- **Confidence:** 1%.

**C. Fixed 50/50 linear blend of LLM and formula with the market excluded, the desk's current combination**
- **Mechanism:** averaging is meant to diversify error.
- **Evidence:** theory says the blend is underconfident and less sharp (Ranjan–Gneiting; Baron). The desk's own data agree: the blend at 0.196 is worse than both the LLM (0.192) and the market (0.182).
- **Is the logic sound?** No. It leaves out the most informative input and fixes the weights by assumption.
- **Confidence:** below 1%.

**D. Market-anchored pooling on slow event markets**
- **What it is:** q = m + w(L − m), or a log-odds version, with w fitted walk-forward. The desk trades only when |q − executable price| exceeds fee + half-spread + a buffer, and sizes at fractional Kelly.
- **Mechanism:** the LLM's errors are partly independent of the market's, so a small weight reduces error.
- **Evidence:** documented accuracy gains (Halawi; AIA). Independent evidence of after-fee profit on Kalshi is missing; the +80% figure is self-reported.
- **Is the logic sound?** Yes. This is standard forecast combination, provided the weight is estimated rather than assumed.
- **Needs to run:** everything in A, plus logged mid, bid and ask at forecast time, and hundreds to thousands of resolved forecasts to fit w.
- **Paper testing:** honest for accuracy when run forward. P&L is honest only for taker fills at displayed size. The binding constraint is the sample needed to estimate w: about 2,800 forecasts for ±0.2 at 95% (section 3).
- **Confidence:** 12%.

**E. Market-anchored pooling on 15-minute crypto**
- Same method as D, but the fitted w is expected to be about 0, and latency makes any small w unexploitable.
- **Confidence:** 2%.

**F. LLM as a disagreement flag or triage tool (slow markets)**
- **What it is:** large gaps between the LLM and the market trigger human or rule-based review. The LLM never sets the price.
- **Mechanism:** it scales attention across many markets, and value comes from catching rule misreads or neglected news.
- **Evidence:** indirect only. The "Beyond Accuracy" crowd-agreement filter improved Sharpe and ROI. Halawi's gains were concentrated where the crowd was uncertain.
- **Is the logic sound?** Yes as a research tool. The edge belongs to the review process, not the LLM.
- **Paper testing:** honest if the desk logs each flag, its decision, later price drift and the outcome.
- **Confidence:** 10%.

**G. LLM as a veto or risk filter on fast markets**
- **What it is:** a no-trade filter for scheduled macro releases, exchange incidents or abnormal news.
- **Evidence:** none found.
- **Is the logic sound?** Yes as risk control, but a veto can only remove trades, so it needs a base strategy that already has an edge. A calendar plus code checks do most of this more cheaply and faster.
- **Paper testing:** honest. Compare the P&L of vetoed and non-vetoed candidates.
- **Confidence:** 3% as an edge source.

**H. Extremizing an LLM-plus-market pool**
- **Mechanism:** corrects pools of forecasters whose information is independent.
- **Evidence:** helps when the forecasters' information is disjoint (Satopää; Neyman). It can push a wrong-sided average further wrong (NYU Abu Dhabi working paper).
- **Is the logic sound?** No, when the LLM has seen the price or the same news.
- **Confidence:** 3%.

**I. Autonomous LLM trading agents**
- **What it is:** the Polymarket agents framework, or Prediction Arena-style agents that choose markets, sizes and timing themselves.
- **Evidence:** real-money losses (Prediction Arena); Alpha Arena losses and overtrading; company-reported Olas results.
- **Is the logic sound?** No. It compounds forecast error with sizing and execution errors.
- **Confidence:** 3%.

**J. Proper-betting or fractional-Kelly layer (belief-to-trade)**
- **What it is:** a sizing and direction rule that uses only the forecast and the market price. Examples are one-quarter Kelly with hard limits (Raven-Agent) and "proper betting" (Gu et al.).
- **Role:** it is not an edge source on its own. It is what turns a real accuracy edge into profit and limits damage when there is none. The positive evidence is the authors' own and preliminary.
- **Confidence:** 8% at system level; the layer itself is recommended as hygiene for any strategy.

**K. LLM-assisted semantic or consistency arbitrage**
- **What it is:** the LLM maps logically related markets (implications, brackets, the same event on Kalshi and Polymarket), and code checks price consistency and fees on both legs.
- **Mechanism:** LLMs are good at reading contract text, and mispricings between related contracts need no forecast of the outcome.
- **Evidence:** relationship accuracy of about 60–70% and about 20% weekly returns (Semantic Trading; unverified). A non-LLM bot that used Kalshi as fair value on Polymarket US made money only from rebates.
- **Is the logic sound?** Yes, but a 30–40% error rate on relationships is dangerous without human checking of the resolution rules, and both legs pay fees.
- **Paper testing:** fairly honest if both legs are filled at displayed size.
- **Confidence:** 12%.

**L. Ensemble of several LLMs as the forecaster**
- **Evidence:** matches average human crowds (Schoenegger) but carries the acquiescence skew, and nothing shows it beats markets.
- **Confidence:** 4%.

**M. Non-LLM: recalibrate the market price toward the extremes, maker side**
- This is outside this note's scope and comes from a single working paper (Bürgi et al.). Other researchers in this effort may cover it.
- **Mechanism:** avoid buying, or sell, the cheapest longshots and favor high-priced contracts as a maker.
- **Is the logic sound?** It rests on a documented bias, but the edge after fees is thin.
- **Confidence:** 25%.

### Gaps
- The scores are judgments based on unverified figures and are not calibrated against outcomes.
- I found no independent, audited Kalshi P&L for any LLM approach.
- K and M depend on execution details (fills on both legs, maker queue position) that these sources do not cover.

## 7. What does the literature imply for the desk's 50/50 Jev blend, given 74 forecasts of 15-minute crypto contracts where the market scored 0.182, Jev 0.192 and the blend 0.196, and the blend was closer to 50/50 than the market two times in three?

### Takeaway
The desk's result is what the literature predicts. On a 15-minute price contract near expiry, the market price is the best available forecast. Jev is shown the market and the formula, so it mostly re-expresses them with noise. A fixed 50/50 linear blend of two forecasts weaker than the market is pulled toward 50%, and on Kalshi that points the desk at overpriced longshots.

What to change:
- Make the market price the anchor.
- Replace the 50/50 weights with a weight fitted out of sample, expected to be about 0.
- Score Jev against the market, not against the base rate.
- Use Jev at most as a veto for information that is not in the price.
- Do not trust any LLM weight until there are thousands of resolved forecasts.

### Cited Findings
**Desk facts (from the repository and the brief)**
- The formula is a driftless lognormal digital: "with no drift and lognormal moves, P(S_T > K) = Phi( ln(S/K) / (sigma * sqrt(tau)) ). Jev is asked only about what this misses." Volatility is per-block realized volatility scaled by sqrt(τ / block length) ([kalshi/model.py](/home/user/Dealbot/kalshi/model.py)).
- Jev's state includes "mkt: the contract's own YES price snapshot" and a contract object with yes_bid, yes_ask, spot, distance_bps and **model_p_yes**. Its questions are:
  - "settles_yes";
  - "pickoff", asking whether the ask is stale;
  - "momentum", asking whether spot moves more than 5 bps toward the strike, away from it, or stays;
  - "danger".

  Source: [questions/kalshi.py](/home/user/Dealbot/questions/kalshi.py).
- Jev sees a deterministic snapshot of under 400 tokens that is safe as of the decision time. The policy buys YES "when the combined probability beats the ask by more than (1 + margin) x (taker fee + half the spread)". Trading is confined to each contract's last KALSHI_TRADE_WINDOW_S seconds. The underlying price is taken from Coinbase ([README.md](/home/user/Dealbot/README.md)).
- The analyst's daily review grades "Jev's calibration where outcomes have resolved (Brier against the base rate)" ([ops/analyst_prompt.md](/home/user/Dealbot/ops/analyst_prompt.md)).
- The 74-forecast scores (market 0.182, Jev 0.192, blend 0.196) and the "closer to 50/50 two times in three" figure come from the requester's brief.

**Literature that bears on it**
- Markets outperform LLMs as resolution approaches ([Prophet Arena](https://proceedings.iclr.cc/paper_files/paper/2026/file/aec5e2847c5ae90f939ab786774856cc-Paper-Conference.pdf)).
- The best LLM forecaster would do better by outputting the market price ([Hindcast](https://arxiv.org/html/2607.14051v1)).
- Fitted LLM weights against a liquid market are 0.2 to about 0.33, on long-horizon event questions ([Halawi](https://proceedings.neurips.cc/paper_files/paper/2024/file/5a5acfd0876c940d81619c1dc60e7748-Paper-Conference.pdf); [AIA](https://arxiv.org/pdf/2511.07678)).
- Linear pools are uncalibrated and less sharp ([Ranjan & Gneiting](https://econpapers.repec.org/RePEc:bla:jorssb:v:72:y:2010:i:1:p:71-91)), and averaging noise pulls toward 0.5 ([Baron et al.](https://econpapers.repec.org/RePEc:inm:ordeca:v:11:y:2014:i:2:p:133-145)).
- LLMs can piggyback on crowd forecasts in their inputs ([Paleka et al.](https://arxiv.org/abs/2506.00723)).
- Kalshi longshots are overpriced, worst for takers ([Bürgi, Deng & Whelan](https://www.karlwhelan.com/Papers/Kalshi.pdf)).
- Naive-mid priors beat feature models on BTC 15-minute books ([OpenMarket](https://arxiv.org/html/2607.26245v1)).
- LLM components add nothing to time-series forecasting ([Tan et al.](https://proceedings.neurips.cc/paper_files/paper/2024/hash/6ed5bf446f59e2c6646d23058c86424b-Abstract.html)).
- The taker fee is round-up(0.07·C·P·(1 − P)) ([DeFi Rate](https://defirate.com/learn/prediction-market-fees/)).

### Inferences
**1. How much weight 74 forecasts can bear (my calculation)**
- For two forecasters, the per-forecast Brier difference has a standard deviation, σ_d, typically about 0.05–0.10 when they differ by 5–10 points.
- The standard error of the mean difference is then σ_d / √74, about 0.006–0.012.
- On that basis the blend's 0.014 gap to the market is about 1.2 to 2.4 standard errors, and Jev's 0.010 gap is about 0.9 to 1.7. That is suggestive, not conclusive.
- It does match a strong prior from the literature, which is that the market wins near resolution.
- The desk can compute σ_d directly from its own 74 paired differences, or run a Diebold–Mariano-style paired test.

**2. The formula is probably the weakest input (my derivation)**
- Squared error is convex, so for a 50/50 linear average in probability space, Brier(blend) ≤ ½ Brier(Jev) + ½ Brier(formula).
- With the blend at 0.196 and Jev at 0.192, the formula's Brier on these 74 must be at least 2 × 0.196 − 0.192 = 0.200, worse than both Jev and the market.
- Averaging also bought almost no diversification. If the formula's Brier was 0.20–0.25, the uncentered correlation between Jev's errors and the formula's errors was about 0.78–1.0. That fits Jev anchoring on the model_p_yes in its snapshot.
- These conclusions hold only if the blend is a linear average of probabilities on the same 74 forecasts. The desk can confirm by computing the formula's Brier directly.

**3. Why the blend sat closer to 50/50 than the market**
- **Mechanical (sourced theory):** a linear average of two forecasts that each carry less information than the market, and sometimes disagree, loses sharpness and drifts toward 0.5 (Ranjan–Gneiting; Baron).
- **Hypotheses about the formula, each to check:**
  - (i) Realized volatility measured on short blocks of Coinbase prices may be inflated by bid-ask bounce, which makes σ√τ too large and the formula underconfident.
  - (ii) If KXBTC15M settles on an average of BRTI over the final seconds or minute, the remaining variance is smaller than σ²τ near expiry. A formula ignoring that would be too close to 50% in exactly the trading window used. This is unverified; read the contract terms.
  - (iii) The formula uses Coinbase, while settlement uses BRTI. That basis gap adds error near the strike.
- **Possible Jev hedging:** this is not documented for LLMs generally; the documented biases are overconfidence and an upward skew. Measure how often Jev alone sits closer to 50% than the market.

**4. The trading consequence**
- A forecast that is closer to 50% than the market always rates the cheaper contract as underpriced. If the market has YES at 80¢ and the blend says 65%, NO at 20¢ looks cheap. The blend's "edges" are therefore concentrated on longshots.
- Kalshi's documented favorite-longshot bias says those are the contracts that lose the most, especially for takers.
- The fee + half-spread threshold filters small gaps, but it does not fix a systematic bias.
- Before trusting any blend signal, check paper P&L by price bucket (for example below 20¢, 20–80¢, above 80¢) and by side.

**5. What the literature implies for using Jev**
- **Make the market mid the default forecast.** Let Jev enter only as a fitted deviation: q = m + w(Jev − m), with w estimated walk-forward from a regression of (outcome − m) on (Jev − m).
  - On 15-minute crypto near expiry, expect w ≈ 0.
  - Until there are at least 2,000–3,000 resolved paired forecasts, cap w low (for example ≤0.1) or set it to zero. With 74, SE(w) ≈ 0.6 (section 3).
- **Take the formula out of the probability blend.** Use it as one feature in the same out-of-sample regression, and as a code-level, millisecond stale-quote detector. Stale quotes are a latency problem; an LLM taking seconds is the wrong tool, so Jev's "pickoff" question is better answered by code.
- **Change Jev's benchmark** from "Brier against the base rate" to Brier against the market mid at the same timestamp, and P&L against the executable ask or bid. The base-rate benchmark makes an LLM that echoes the price look skilled (Paleka's piggybacking point).
- **If Jev is kept at all, use it as a veto** for things that are not in the price: scheduled macro releases inside the window, exchange or feed incidents, abnormal news. Measure the veto's value as the paper P&L of vetoed versus non-vetoed candidates.
- **Do not extremize.** Jev's information overlaps the market's, so extremizing has no basis here.
- **Fee rounding (my calculation):** a 1-contract order at 50¢ pays 2¢ in fees, against 1.75¢ at 100 contracts. Keep the desk's ORDER_QTY in mind when computing the threshold.
- **Plan sample sizes up front (my calculation).** A contract bought near 50¢ has a payoff standard deviation of about 50¢. Detecting an edge at two standard errors therefore needs about 10,000 independent trades for 1¢ per contract, about 2,500 for 2¢, about 1,100 for 3¢ and about 400 for 5¢. BTC and ETH contracts in the same window are correlated and count as fewer independent samples. Pre-register the test before running it.

### Gaps
- The brief does not give the base rate, when within each window the 74 forecasts were made, Jev's distance from 50% on its own, the formula's own Brier, or σ_d, so the calculations above are bounds and assumptions to replace with desk data.
- KXBTC15M settlement mechanics (BRTI averaging window) were not verified.
- No source tests an LLM veto on fast crypto contracts.
