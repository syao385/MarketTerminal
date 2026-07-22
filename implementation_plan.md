# Implementation Plan - Aether Market Terminal (Updated)

This document describes the final production architecture, features, API integrations, and validation metrics implemented in the Aether Market Terminal.

---

## 1. High-Fidelity Bloomberg-Style UI Grid
The application is implemented as a single-page, serverless terminal in [index.html](file:///c:/Users/jfan/Documents/MarketTerminal/index.html) running entirely in the browser. It features a responsive dark-themed grid system split into three key panels:

1. **Header Panel:**
   - Real-time market clock locked to US Eastern Time (EST).
   - Market hours status banner (`LIVE` in green vs. `CLOSED` in red) auto-determined by trading hours and holiday schedules.
   - Financial portfolio balance summary ($10,000 simulated cash) and real-time P&L trackers.
   - Settings Modal trigger to configure Gemini API Key, Gemini Model, and Finnhub API Key.

2. **Left Panel (Watchlist & Scanners):**
   - **Watchlist Table:** Interactive tickers (AAPL, NVDA, TSLA, etc.) showing real-time price tick indicators, daily percentage change, and volume. Click-to-load updates the chart, trade terminal, and sentiment views.
   - **Premarket Gappers:** Real-time premarket scanner scraping top gainers from Yahoo Finance (filter criteria: Gap > 5%, Price > $3, Volume > 50,000). Features a direct catalyst headline loader.
   - **Top 10 In-Play Tickers:** Dynamic lists compiled via Gemini AI (or hardcoded backup) highlighting active catalyst reasons.

3. **Center Panel (Charting, Execution & Analyst):**
   - **Interactive Chart:** Embedded TradingView widget showing price and volume candles. Falls back to a custom HTML5 Canvas drawing system if TradingView CDN is offline.
   - **Trade Terminal Form:** Support for BUY/SELL orders with auto cost calculation, holdings text updates, and Cash limit flags.
   - **Positions & History:** Real-time holdings tracker (average cost, live P&L, Liquidation button) and completed transactions ledger.
   - **Gemini Institutional Analyst:** Single-button click triggers a 3-sentence read from Gemini AI summarizing price momentum, technical risk factors, and watch levels.

4. **Right Panel (Multi-Feed News & Macro Flows):**
   - **Multi-Feed News Stream:** Tab selector toggling feeds (ALL, WSJ, CNBC, Reddit, Google News, or Finnhub general/company feeds). Includes clickable tag filter badges (Trump, Fed, Econ, Tickers).
   - **Divergence Sentiment Bar:** Renders the ratio of positive/bearish/neutral items. Contrasts mainstream institutional reporting against retail social sentiment.
   - **Macro Flow & Surveys Dashboard:** Tracks the AAII Sentiment Survey, NAAIM Exposure Index, UMich Consumer Sentiment, and a composite SMI (Systemic Macro Index) with a sparkline.
   - **Weekly Fund Flows Indicator:** Custom quantitative index mapping money flow standard deviations and momentum signals.

---

## 2. API Integration & Routing Architecture

### CORS Bypass & Caching Proxy
- Standard RSS feeds and Yahoo Finance APIs are routed through a local node proxy ([proxy-server.js](file:///c:/Users/jfan/Documents/MarketTerminal/proxy-server.js)) running at `http://127.0.0.1:3000` (started via [start-proxy.bat](file:///c:/Users/jfan/Documents/MarketTerminal/start-proxy.bat)).
- **Cache Layer:** The proxy server implements a **2-minute (120,000 ms) in-memory cache** to prevent duplicate external requests.
- **Failover:** If the local proxy is offline, the client auto-detects the state and falls back to public CORS proxies (`corsproxy.io` and `api.allorigins.win`) or Finnhub native CORS calls.

### Startup Default Ticker
- The terminal is configured to load **`QQQ`** (Invesco QQQ Trust ETF) by default on launch instead of `AAPL`. This initializes all charts, sentiment indicators, and trading badges automatically on boot.

---

## 3. Custom Quantitative Scrapers & Fallback Engines

### Premarket Gapper Catalyst Flow (Optimized Batch AI)
To achieve fast, reliable, and token-efficient catalyst loading for all 10 gapper symbols, the scanner runs a hybrid pipeline:
1. **Gemini Batch AI Query:** If a Gemini API Key is configured, the scanner performs a **single batch query** to `gemini-3.6-flash` with Google Search Grounding for all 10 symbols at once, returning a JSON mapping of symbols to precise catalyst summaries (mentioning if they are rising/falling).
2. **Fallback Hierarchical Scraper:** If the batch query fails, is rate-limited, or no key is present, it falls back to the sequential local parser loop:
   - **Google News RSS:** Queries Google News RSS via local proxy. If a headline under 24 hours old is found, renders it directly.
   - **Yahoo News RSS:** Queries Yahoo News RSS via local proxy. If a headline under 24 hours old is found, renders it.
   - **Benzinga Scraper:** Parses Benzinga quote pages to extract recent headlines.
   - **Gemini Fallback:** Calls Gemini to synthesize a 1-sentence summary of the accumulated text.
3. **Neutral Default:** Displays `<span style="color:var(--txt-sec);">No catalyst.</span>` in grey if all paths return empty.

### Weekly Fund Flows Z-Score & Turning Point Index
To replace the hardcoded `"Unavailable"` flows text in direct scraping mode, we calculate a **Weekly ETF Money Flow Proxy** using Yahoo Finance chart data for **SPY** (Equity), **TLT** (Bond), and **BIL** (Cash):
- **Daily Flow Formula:**
  $$\text{Daily Flow} = \text{Volume} \times \text{Closing Price} \times \text{Daily Price Change \%}$$
- **Rolling Sum:** Computes 5-day sums across a 30-day daily chart.
- **Z-Score Normalization:** Normalized using mean and standard deviation:
  $$Z = \frac{\text{Current Week} - \text{Mean}}{\text{StdDev}}$$
- **Reversal Detection:** Identifies momentum signals by comparing current vs. previous week's flows:
  - *Bullish Reversal:* Flow turned from negative to positive.
  - *Bearish Reversal:* Flow turned from positive to negative.
  - *Inflow / Outflow Acceleration or Deceleration.*
- **Output format:** `Eq: Z: +0.24 (Bullish Reversal) | Bd: Z: -0.24 (Outflow Decel) | Cash: Z: +0.34 (Inflow Decel)`.

---

## 4. Verification & Testing

The terminal is validated using the following manual checklist:
1. **Startup Check:** Open index.html in a web browser. Confirm the page boots immediately loading QQQ as the active asset.
2. **Gapper Scanner:** Trigger premarket scans. Verify that catalysts render immediately for stocks with fresh news, and show "No catalyst" for others without calling Gemini.
3. **Macro Refresh:** Switch to the Macro tab and click refresh. Verify that AAII, NAAIM, and UMich show scraped numbers, while Weekly Fund Flows renders computed Z-scores.
4. **Trade Lifecycle:** Execute buy and sell trades. Verify that the portfolio value updates on Watchlist price fluctuations (every 60 seconds).
