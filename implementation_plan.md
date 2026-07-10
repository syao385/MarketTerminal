# Implementation Plan - Aether Market Terminal

We will build a high-fidelity, single-file serverless Market Terminal in `index.html`. It will run entirely in the browser with no framework, build step, or backend. The terminal features a Bloomberg-style dark UI, real-time news feeds with automated proxy rotation, keyword tagging, sentiment analysis, Yahoo Finance quote/chart retrieval, TradingView interactive charts, Gemini AI stock analyst summaries, and a full paper-trading simulator saved in `localStorage`.

---

## Proposed Changes

### [NEW] [index.html](file:///c:/Users/jfan/Documents/MarketTerminal/index.html)
This single file will contain all structure (HTML5), styles (CSS3), and application logic (ES6 JavaScript).

#### Key Components:
1. **HTML Layout (Bloomberg-style grid)**:
   - **Header**: System status, Market Hours status (Live/Closed), API Key configuration, and Portfolio Balance summary ($1,000 initial).
   - **Left Panel (Watchlist & Trading)**:
     - Watchlist with current prices and daily changes (AAPL, NVDA, TSLA, MSFT, SPY, etc.).
     - Paper Trading Terminal: Buy/Sell form (Market orders filled instantly), Position tracker, and transaction history.
   - **Center Panel (Chart & AI Analysis)**:
     - Interactive chart window supporting timeframe toggles (1D Intraday vs 1M Daily).
     - Live quote detail widget (Open, High, Low, Close, Volume).
     - AI Analyst Terminal with "Run Deep Dive" powered by the Gemini 2.5 Flash API.
   - **Right Panel (News & Social Sentiment)**:
     - **Multi-Feed Viewer**: Tabs to toggle between different news streams:
       - **Wall Street Journal**: `https://feeds.a.dj.com/rss/RSSMarketsMain.xml` (Best for: Markets headlines)
       - **CNBC**: `https://search.cnbc.com/rs/search/combinedcms/view.xml` (Best for: Business / breaking news)
       - **Google News (Custom Search Query)**: `https://news.google.com/rss/search?q=YOUR_QUERY` (Best for: Any specific topic, ticker, premarket, Fed, 13F, etc.)
       - **Reddit r/stocks**: `https://www.reddit.com/r/stocks/hot.rss` (Best for: Retail sentiment)
       - **Reddit r/wallstreetbets**: `https://www.reddit.com/r/wallstreetbets/hot.rss` (Best for: Momentum / market buzz)
     - **Sentiment Indicators & Tagging**: Automatic keyword tagging (Econ, Politics, Buzz, Insider, Tech) and positive/negative sentiment tagging based on headline text.
     - **Trending Tickers Board**: Auto-parsed ticker mentions from the active headlines to show social/news momentum.

2. **Styling & Aesthetics (Genesis Design System)**:
   - **Colors**: Quietly confident warm light mode.
     - Background: `#FAFAFA` (light warm gray)
     - Surface: `#FFFFFF` (white cards, panels, nav backdrop)
     - Text Primary: `#0A0A0A` (near-black, bold headings)
     - Text Secondary: `#6B6B6B` (metadata, descriptions)
     - Primary: `#6366F1` (indigo for CTAs, active states, focus rings, highlights)
     - Primary Hover: `#4F46E5` (darker indigo)
     - Neutral/Border: `#E8E8EC` (recessive card borders and inputs)
     - Semantic: `#10B981` (success/gains), `#EF4444` (error/losses), `#F59E0B` (warning/pending)
   - **Typography**:
     - Display Font: General Sans (loaded from Fontshare CDN) at bold weight with tight letter spacing (`-0.03em`) for headers and logo.
     - Body Font: DM Sans (loaded from Google Fonts) for UI text, tables, and news body.
     - Code Font: JetBrains Mono (loaded from Google Fonts) for terminal logs, API keys, and ticker indicators.
   - **Elevation & Radius**:
     - Cards rest flat with 1px border (`#E8E8EC`) and 12px border radius. Lifts `-2px` on hover with a subtle shadow (`0 8px 30px rgba(0,0,0,0.08)`).
     - Buttons and inputs have a 6px border radius. Focus states gain a 3px indigo glow ring (`0 0 0 3px rgba(99,102,241,0.12)`).
     - Navigation uses a sticky top nav (56px height) with a 1px bottom border and glassmorphic `backdrop-filter: blur(12px)` over `#FFFFFF`.

3. **Data & APIs (Client-side)**:
   - **Data Fetching & Proxy Strategy**:
     - Standard RSS feeds (WSJ, CNBC, Google News) and Yahoo Finance data will be fetched using AllOrigins raw proxy (`https://api.allorigins.win/raw?url=`).
     - Reddit RSS feeds (r/stocks, r/wallstreetbets) will be fetched using the free `rss2json` API (`https://api.rss2json.com/v1/api.json?rss_url=`). This bypasses Reddit's strict block on standard raw CORS proxies by utilizing `rss2json`'s server-side user-agent rotation and caching.
     - Fallback: If any RSS feed fails, the UI will fall back to using Google News query feeds (e.g., `https://news.google.com/rss/search?q=site:reddit.com/r/stocks` for Reddit) routed through AllOrigins, ensuring continuous feed availability.
   - **Yahoo Finance API Integration**:
     - Fetched via the CORS proxy from Yahoo Finance's unofficial chart/quote endpoint.
     - Provides real-time quotes, watchlist prices, and historical/intraday chart data.
   - **Interactive Charting**:
     - TradingView Lightweight Charts (loaded via CDN) for pixel-perfect price and volume candlestick/line charts.
     - Fallback SVG/Canvas chart in case the CDN is blocked or offline.
   - **Gemini AI Analyst**:
     - Queries `gemini-2.5-flash-lite` (or `gemini-2.5-flash`) using the user's API key (stored in `localStorage` or falling back to the default key).
     - Formats prompt for 3-sentence read on momentum, risks, and watches.
   - **Paper Trading Engine**:
     - Persists balance, active holdings (ticker, volume, avg cost), and transaction history in `localStorage`.
     - Simulates instant market orders based on Yahoo Finance real-time prices.
     - Dynamically calculates portfolio value and P&L based on active quotes.

---

## Resolved Questions & Technical Alignment

1. **Reddit User-Agent/Proxy limits**: Resolved by using `rss2json.com` as the primary fetcher for Reddit feeds (verified via PowerShell testing that it successfully returns parsed JSON data). Fallback is Google News search indexing Reddit.
2. **Gemini API Key Configuration**: The terminal only requires a Gemini API key to run stock deep-dives. We will pre-populate the key field with the key provided in the prompt, and add a Settings panel that allows the user to paste their own key (saved in `localStorage` client-side). We'll add instructions on how to find the key at Google AI Studio (https://aistudio.google.com).

---

## Verification Plan

### Manual Verification
1. Open `index.html` in Chrome/Edge.
2. Verify all layouts load and Lucide icons render.
3. Test watchlist loading and search (e.g. type `AAPL`, verify prices, and chart updates).
4. Verify news tabs pull and tag headlines (verify green/red sentiment dots and custom tags like `buzz` or `insider`).
5. Execute a paper trade (Buy 5 shares of `NVDA`): verify balance decreases, positions table updates, and P&L starts tracking.
6. Trigger an AI analyst analysis (verify loading state, typewriter effect, and returned summary text).
7. Refresh the page to verify paper trading portfolio state and API key persist.
