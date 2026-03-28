# Portfolio Dashboard — README
 
A personal portfolio tracking dashboard built with Streamlit, yFinance, and Plotly. It fetches live market data, computes risk and return metrics, visualises concentration risk, and runs an AI strategy agent via Google Gemini. 

---
 
## Holdings Table
 
The table gives a per-asset snapshot of every position in the portfolio. Each column is explained below.
 
### ROI (%)
 
Return on investment since the date of purchase.
 
```
ROI = (Current Value − Cost Basis) / Cost Basis × 100
```
 
Cost basis is computed by matching each ledger entry (date + quantity) to the closest historical price using `pd.merge_asof`, so purchases made at different times are individually costed and then summed.
 
### Unrealised Profit ($)
 
The dollar gain or loss if the position were closed today.
 
```
Unrealised P&L = (Latest Price × Quantity Held) − Cost Basis
```
 
This is "unrealised" because no sale has taken place; it is a mark-to-market figure.
 
### MoM (%) — Month-on-Month
 
Price change over the last 30 calendar days.
 
```
MoM = (Price_today − Price_30d_ago) / Price_30d_ago × 100
```
 
### YoY (%) — Year-on-Year
 
Price change over the last 365 calendar days, using the same formula scaled to a one-year window.
 
### Ann. Volatility (%)
 
Annualised historical volatility, the standard industry measure of price risk. Computed as the 30-day rolling standard deviation of daily returns, then scaled to one year:
 
```
σ_annual = σ_daily_30d × √252
```
 
The factor √252 comes from the square-root-of-time rule for independent returns: because there are approximately 252 trading days in a US equity year, daily volatility scales to annual volatility by multiplying by the square root of that count. This is the standard convention across equity markets, options pricing (Black-Scholes), and risk systems. See [Wikipedia — Volatility (finance)](https://en.wikipedia.org/wiki/Volatility_(finance)) and Hull, *Options, Futures, and Other Derivatives* (any edition), Chapter 15.
 
### Portfolio Weight (%)
 
The share of total portfolio market value attributable to each asset on the most recent trading day.
 
```
Weight_i = Market_Value_i / Σ Market_Value × 100
```
 
---
 
## Risk Matrix
 
The risk matrix is a two-dimensional scatter plot that maps every holding along two axes simultaneously:
 
| Axis | Variable | What it captures |
|------|----------|-----------------|
| X (horizontal) | Ann. Volatility (%) | How much the asset's price swings — a proxy for individual asset risk |
| Y (vertical) | Portfolio Weight (%) | How much capital is concentrated in that asset |
| Bubble size | Unrealised P&L ($) | How much profit is currently at stake in that position |
| Bubble colour | ROI bracket | Overall performance since purchase |
 
### Why these two axes?
 
Risk in a portfolio has two distinct sources. The first is the **riskiness of the individual asset** — how volatile its price is. The second is **concentration** — how large a share of your total capital it represents. An asset can be individually low-risk but still pose a danger if it accounts for 60% of your portfolio, and vice versa. Plotting both dimensions at once lets you see which assets are dangerous for which reason.
 
This logic is grounded in Modern Portfolio Theory (MPT). Markowitz (1952) formalised the idea that portfolio risk cannot be assessed by looking at individual assets in isolation; it depends on both each asset's own variance and its weight in the portfolio. The variance of a two-asset portfolio is:
 
```
σ²_p = w₁²σ₁² + w₂²σ₂² + 2w₁w₂σ₁₂
```
 
where `w` is the portfolio weight and `σ₁₂` is the covariance between assets. The risk matrix visualises the `w²σ²` terms — the interaction of weight and volatility — without requiring a full covariance matrix.
 
> Markowitz, H. (1952). *Portfolio Selection*. **The Journal of Finance**, 7(1), 77–91.
 
### The Four Quadrants
 
The matrix is divided into quadrants by threshold lines at **25% volatility** and **25% portfolio weight**. These thresholds are heuristic and intended as conversation-starters, not hard regulatory limits. They are, however, informed by established risk frameworks:
 
| Quadrant | Volatility | Weight | Interpretation |
|----------|-----------|--------|----------------|
| **Low Risk** (bottom-left) | < 25% | < 25% | Asset is both calm and small — low urgency |
| **High Vol** (bottom-right) | > 25% | < 25% | Asset is risky but position is small — monitor |
| **Concentrated** (top-left) | < 25% | > 25% | Asset is calm but you hold a lot — rebalance candidate |
| **Danger Zone** (top-right) | > 25% | > 25% | High volatility AND high exposure — highest priority |
 
#### Concentration thresholds — regulatory context
 
The 25% weight threshold as a soft warning level is consistent with how institutional regulators think about large exposures. The Basel Committee on Banking Supervision (BCBS) defines a **large exposure** as any single counterparty exposure equal to or above **10% of eligible capital** and sets a hard cap at **25% of Tier 1 capital** for banks. While the dashboard applies to a retail equity portfolio rather than a bank balance sheet, these thresholds reflect the same underlying principle: concentration in any single name amplifies loss given an adverse event.
 
> BIS / BCBS (2014). *Supervisory framework for measuring and controlling large exposures* (BCBS 283). Bank for International Settlements. [https://www.bis.org/publ/bcbs283.pdf](https://www.bis.org/publ/bcbs283.pdf)
 
> BIS / BCBS (2006). *Studies on credit risk concentration* (BCBS Working Paper 15). Bank for International Settlements. [https://www.bis.org/publ/bcbs_wp15.pdf](https://www.bis.org/publ/bcbs_wp15.pdf)
 
The BCBS also identifies **sector concentration** — overweight exposure to a single industry or asset class — as a key risk that sits outside the standard Pillar 1 minimum capital model, requiring supervisory review under Pillar 2. For a retail investor, an analogous concern is being overweight a single ticker.
 
> BIS / BCBS (2009). *Range of practices and issues in economic capital frameworks* (BCBS 152). Bank for International Settlements. [https://www.bis.org/publ/bcbs152.pdf](https://www.bis.org/publ/bcbs152.pdf)
 
#### Volatility thresholds — common market convention
 
A 25% annualised volatility threshold is a widely used informal boundary in equity risk management:
 
- Below ~15–20%: typical for investment-grade bonds, defensive equities, and broad index ETFs.
- 20–35%: typical range for individual large-cap equities.
- Above 35–40%: common for small-caps, growth stocks, commodities, and crypto.
 
No single official standard mandates a universal threshold; the 25% line used here is a practical midpoint that separates broadly "calm" assets from "elevated-risk" assets in the context of a mixed portfolio. The Basel market risk framework (FRTB, BCBS 457) uses its own internally calibrated stress scenarios rather than a fixed volatility cutoff, but the principle — distinguishing assets by their price-movement risk — is the same.
 
> BIS / BCBS (2019). *Minimum capital requirements for market risk* (BCBS 457 / FRTB). Bank for International Settlements. [https://www.bis.org/bcbs/publ/d457.pdf](https://www.bis.org/bcbs/publ/d457.pdf)
 
### Bubble Size — Unrealised P&L
 
The bubble size encodes how much money is currently at stake in each position. A large green bubble in the Danger Zone means you have significant gains that could be at risk if that volatile, concentrated position turns. A small bubble in the same zone is less urgent. This gives a third dimension of decision-making priority beyond the two axes alone.
 
### Colour Coding — ROI Brackets
 
| Colour | ROI range | Meaning |
|--------|-----------|---------|
| Green | ≥ 20% | Strong performer — consider whether to take some profit |
| Blue | 0 – 20% | Moderate gain — hold and monitor |
| Amber | −10 – 0% | Slight loss — watch closely |
| Red | < −10% | Significant loss — review thesis |
 
---
 
## Strategy Agent
 
The AI agent (Google Gemini 2.5 Flash Lite via Google ADK) reads the 30-day aggregated portfolio summary and applies a deterministic decision tree to produce one of four signals per ticker: **BUY**, **SELL**, **HOLD**, or **REBALANCE**. The rules are:
 
| Priority | Condition | Signal |
|----------|-----------|--------|
| 1 | ROI > 500% AND weight > 20% | SELL |
| 2 | Weight > 30% | REBALANCE |
| 3 | Volatility > 40% AND 30d price change < −5% | SELL |
| 4 | Volatility < 15% AND 30d change > 0% AND weight < 10% | BUY |
| 5 | Otherwise | HOLD |
 
The agent produces a plain-English explanation citing the actual numbers for each ticker. **This is not financial advice.**
 
---
 
## Data Sources
 
| Source | Used for |
|--------|---------|
| [yFinance](https://github.com/ranaroussi/yfinance) | Historical and current price data (Yahoo Finance) |
| `financial_ledger.csv` | Purchase dates, tickers, quantities |
| Google Gemini 2.5 Flash Lite (via Google ADK) | Strategy agent text generation |
 
Price data is cached for 1 hour (`@st.cache_data(ttl=3600)`).
 
---
 
## Key Academic & Regulatory References
 
| Reference | Relevance |
|-----------|-----------|
| Markowitz, H. (1952). *Portfolio Selection*. **The Journal of Finance**, 7(1), 77–91. | Theoretical basis for volatility × weight as the joint determinants of portfolio risk |
| BIS/BCBS (2014). *Supervisory framework for measuring and controlling large exposures* (BCBS 283). | Source of the 10% / 25% concentration thresholds used to calibrate the quadrant boundaries |
| BIS/BCBS (2006). *Studies on credit risk concentration* (BCBS WP 15). | Framework linking name/sector concentration to economic capital requirements |
| BIS/BCBS (2009). *Range of practices in economic capital frameworks* (BCBS 152). | Concentration risk as a Pillar 2 supervisory concern outside standard Pillar 1 models |
| BIS/BCBS (2019). *Minimum capital requirements for market risk — FRTB* (BCBS 457). | Market risk standard using stress-based volatility measurement; context for volatility as a regulatory risk metric |
| Hull, J. (2022). *Options, Futures, and Other Derivatives* (11th ed.). Pearson. | Standard textbook derivation of the √252 annualisation convention |
 
---
 
## Disclaimer
 
This dashboard is for personal educational and informational use only. It does not constitute financial advice nor represents my professional occupation.